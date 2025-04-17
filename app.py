# app.py (Main Application)
import os
import json
import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from data_processor import DataProcessor
from model_handler import GroqModelHandler
from utils import load_config, setup_logger
from database import DatabaseManager
import sqlite3
# Add to existing imports
db = DatabaseManager()

# Load configurations and environment
load_dotenv()
config = load_config('config.json')
logger = setup_logger()

class ChatBot:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.data_processor = DataProcessor()
        self.model_handler = GroqModelHandler(self.client)
        self.initialize_session()
        self.initialize_auth()
    def initialize_auth(self):
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = None

    def render_user_auth(self):
        st.subheader("User Authentication")
        if st.session_state.user_id:
            st.write(f"Welcome User {st.session_state.user_id}")
            if st.button("Logout"):
                self.logout()
            return
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                self.handle_login(username, password)
        with col2:
            if st.button("Register"):
                self.handle_registration(username, password)

    def handle_login(self, username, password):
        user_id = db.verify_user(username, password)
        if user_id:
            session_id = db.create_session(user_id)
            st.session_state.user_id = user_id
            st.session_state.session_id = session_id
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

    def handle_registration(self, username, password):
        if not username or not password:
            st.error("Please enter username and password")
            return
        try:
            user_id = db.create_user(username, password)
            st.success("Registration successful! Please login")
        except sqlite3.IntegrityError:
            st.error("Username already exists")

    def logout(self):
        st.session_state.user_id = None
        st.session_state.session_id = None
        st.session_state.history = []
        st.rerun()

    def process_user_input(self, prompt):
        # Rate limiting check
        if not db.check_rate_limit(st.session_state.user_id, limit=10, window=60):
            st.error("Rate limit exceeded (10 requests/minute)")
            return
            
        # Save user message
        db.save_message(st.session_state.user_id, "user", prompt)
        
        # Existing processing
        try:
            response = self.generate_response(prompt)
            # Save assistant response
            db.save_message(st.session_state.user_id, "assistant", response)
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            st.error("Failed to generate response. Please try again.")

    def render_chat_interface(self):
        # Load history from database
        if st.session_state.user_id:
            history = db.get_history(st.session_state.user_id)
            st.session_state.history = history[::-1]  # Reverse for display

    def initialize_session(self):
        if "history" not in st.session_state:
            st.session_state.history = []
        if "dataset" not in st.session_state:
            st.session_state.dataset = None
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = None

    def render_sidebar(self):
        with st.sidebar:
            st.title("Configuration")
            st.session_state.model_name = st.selectbox(
                "Select Model",
                config['available_models'],
                index=0
            )
            st.session_state.temperature = st.slider(
                "Temperature", 0.0, 1.0, config['default_temp'], 0.1
            )
            st.session_state.max_tokens = st.slider(
                "Max Tokens", 256, 8192, config['default_max_tokens'], 128
            )
            self.render_dataset_upload()
            self.render_user_auth()

    def render_dataset_upload(self):
        st.subheader("Dataset Management")
        uploaded_files = st.file_uploader(
            "Upload Knowledge Base",
            type=["pdf", "txt", "csv"],
            accept_multiple_files=True
        )
        if uploaded_files:
            with st.spinner("Processing documents..."):
                st.session_state.dataset = self.data_processor.process_files(uploaded_files)
                st.session_state.vector_store = self.data_processor.create_vector_store(
                    st.session_state.dataset
                )
            st.success(f"Processed {len(uploaded_files)} files!")

    def render_user_auth(self):
        st.subheader("User Authentication")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            # Implement proper authentication logic
            st.success(f"Welcome {username}!")

    def render_chat_interface(self):
        st.title(config['app_title'])
        st.markdown(config['app_description'])

        for message in st.session_state.history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask me anything..."):
            self.process_user_input(prompt)

    def process_user_input(self, prompt):
        st.session_state.history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = self.generate_response(prompt)
                st.session_state.history.append({"role": "assistant", "content": response})
            except Exception as e:
                logger.error(f"API Error: {str(e)}")
                st.error("Failed to generate response. Please try again.")

    def generate_response(self, prompt):
        context = ""
        if st.session_state.vector_store:
            context = self.data_processor.retrieve_context(
                prompt, 
                st.session_state.vector_store,
                top_k=config['retrieval_top_k']
            )

        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"
        
        return self.model_handler.generate(
            prompt=full_prompt,
            model_name=st.session_state.model_name,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            stream=True
        )

if __name__ == "__main__":
    st.set_page_config(page_title="Enterprise AI Chatbot", layout="wide")
    chatbot = ChatBot()
    chatbot.render_sidebar()
    chatbot.render_chat_interface()