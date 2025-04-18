import streamlit as st
import os
import json
from dotenv import load_dotenv

# Make sure set_page_config is the very first Streamlit command
st.set_page_config(
    page_title="MediAssist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configurations and environment
try:
    load_dotenv()
except:
    pass  # Handle case where dotenv is not installed

# Define configuration
config = {
    'app_title': "MediAssist AI: Your Personal Medical Assistant",
    'app_description': "Get reliable medical information, symptom analysis, and health guidance from our AI-powered healthcare assistant.",
    'available_models': ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
    'recent_queries': [
        "What are the symptoms of diabetes?",
        "How to read blood test results...",
        "Common side effects of antibiotics...",
        "Diet recommendations for hypertension..."
    ],
    'favorite_queries': [
        "First aid for minor burns...",
        "Understanding cholesterol levels...",
        "Exercise routines for back pain..."
    ]
}

# Define CSS
css = """
/* Base styling for the entire app */
body {
    background-color: #0f1117;
    color: white;
}

/* Main area styling */
.main .block-container {
    padding-top: 0;
    padding-bottom: 0;
    max-width: 100%;
    background-color: #0f1117;
    color: white;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #1a1d26;
}

/* Custom sidebar header */
.sidebar-header {
    color: white;
    padding: 15px 0 15px 0;
    margin: 0;
    font-size: 20px;
    font-weight: bold;
    display: flex;
    align-items: center;
}

/* Configuration section styling */
.config-section {
    margin-bottom: 30px;
}

.config-section h3 {
    color: white;
    font-size: 18px;
    margin-bottom: 15px;
}

/* Dropdown styling */
.stSelectbox > div > div > div {
    background-color: #1E2130 !important;
    border: 1px solid #f54242 !important;
    color: white !important;
}

.stSelectbox > div > div {
    background-color: transparent !important;
}

/* Sidebar item styling */
.sidebar-item {
    padding: 10px 0;
    display: flex;
    align-items: center;
    color: #e0e0e0;
    text-decoration: none;
    margin: 5px 0;
}

.sidebar-item:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.sidebar-icon {
    margin-right: 10px;
    width: 24px;
    text-align: center;
}

/* Section titles */
.section-title {
    color: #e0e0e0;
    font-size: 14px;
    margin: 20px 0 10px 0;
    display: flex;
    align-items: center;
}

/* Recent/Favorites items */
.history-item {
    padding: 5px 0;
    color: #b0b0b0;
    font-size: 14px;
    cursor: pointer;
    transition: color 0.2s;
}

.history-item:hover {
    color: white;
    text-decoration: underline;
}

/* Chat message styling */
.stChatMessage {
    background-color: #1e2130 !important;
    border-radius: 5px !important;
    border: 1px solid #2d303e !important;
    padding: 10px !important;
}

.stChatMessage [data-testid="StyledAvatar"] {
    background-color: #4cc9f0 !important;
}

/* Custom chat input styling to match the image */
.stChatInputContainer {
    background-color: #131417 !important;
    border-radius: 0 !important;
    border: none !important;
    padding: 8px 16px !important;
    width: 100% !important;
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 999 !important;
}

.stChatInputContainer textarea {
    background-color: transparent !important;
    color: #cccccc !important;
    border: none !important;
    padding: 10px 0 !important;
    font-size: 16px !important;
}

/* File uploader custom styling */
.css-1x8cf1d {
    background-color: #131417 !important;
    border-radius: 5px !important;
    border: 1px solid #303243 !important;
    padding: 20px !important;
}

[data-testid="stFileUploader"] {
    width: 100% !important;
}

[data-testid="stFileUploader"] label {
    color: white !important;
    font-weight: 600 !important;
}

[data-testid="stFileUploader"] p {
    color: #b0b0b0 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background-color: #1a1d26 !important;
    border: 1px dashed #303243 !important;
    padding: 15px !important;
}

[data-testid="stFileUploaderDropzone"] p {
    color: #cccccc !important;
}

.css-1offfwp {
    border-radius: 5px !important;
    background-color: #1a1d26 !important;
    color: white !important;
    border: 1px solid #303243 !important;
}

/* Button in file uploader */
[data-testid="stFileUploaderDropzone"] button {
    background-color: #303243 !important;
    color: white !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}

/* Remove default Streamlit padding */
.css-18e3th9 {
    padding-top: 0;
    padding-bottom: 0;
}

/* Hide unnecessary Streamlit components */
#MainMenu, footer, header {
    visibility: hidden;
}

/* Center the title */
h1 {
    text-align: center !important;
    color: white !important;
    font-size: 28px !important;
    margin-bottom: 10px !important;
}

/* Center the description */
.app-description {
    text-align: center !important;
    color: #b0b0b0 !important;
    margin-bottom: 20px !important;
}

/* Style for the model selection dropdown */
div[data-baseweb="select"] {
    background-color: #1e2130 !important;
    border-radius: 5px !important;
    border: 1px solid #f54242 !important;
}

/* Add padding at the bottom to accommodate fixed chat input */
.main-content {
    padding-bottom: 70px !important;
}

/* Make room for attachment icon in chat input */
.attachment-icon {
    position: absolute !important;
    left: 15px !important;
    bottom: 10px !important;
    color: #999 !important;
    font-size: 20px !important;
    z-index: 1000 !important;
}
"""

# Apply CSS
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

class MedicalChatbot:
    def __init__(self):
        self.initialize_session()
        self.setup_ui()
    
    def initialize_session(self):
        if "history" not in st.session_state:
            st.session_state.history = []
        if "dataset" not in st.session_state:
            st.session_state.dataset = None
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = None
        if "model_name" not in st.session_state:
            st.session_state.model_name = config['available_models'][0]
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
        if "pending_query" not in st.session_state:
            st.session_state.pending_query = None
    
    def handle_query_click(self, query):
        """Handle when a user clicks on a recent or favorite query"""
        st.session_state.pending_query = query
        # Force a rerun to submit the query
        st.rerun()
    
    def setup_ui(self):
        # Sidebar
        with st.sidebar:
            # Configuration Section
            st.markdown('<div class="sidebar-header">Configuration</div>', unsafe_allow_html=True)
            
            # Model Selection
            st.markdown("<div style='margin-top: 10px;'>Select Model</div>", unsafe_allow_html=True)
            model_name = st.selectbox(
                "",
                config['available_models'],
                index=0,
                key="model_selector",
                label_visibility="collapsed"
            )
            st.session_state.model_name = model_name
            
            # Divider
            st.markdown('<hr style="margin: 15px 0; border-color: #2d303e;">', unsafe_allow_html=True)
            
            # Dataset Management section styled to match Image 1
            st.markdown('<div class="sidebar-header">Dataset Management</div>', unsafe_allow_html=True)
            
            # File uploader with custom styling
            uploaded_files = st.file_uploader(
                "Upload Knowledge Base",
                type=["pdf", "txt", "csv"],
                accept_multiple_files=True,
                help="Limit 200MB per file • PDF, TXT, CSV"
            )
            
            if uploaded_files:
                with st.spinner("Processing documents..."):
                    # Placeholder for processing - would use data_processor in real implementation
                    pass
                st.success(f"Processed {len(uploaded_files)} files!")
            
            # Divider
            st.markdown('<hr style="margin: 15px 0; border-color: #2d303e;">', unsafe_allow_html=True)
            
            # Recent section with clickable items
            st.markdown('<div class="section-title">Recent ▾</div>', unsafe_allow_html=True)
            
            # Create clickable buttons that look like text for recent queries
            for query in config['recent_queries']:
                if st.button(query, key=f"recent_{query}", 
                            help="Click to ask this question",
                            use_container_width=True,
                            type="secondary"):
                    self.handle_query_click(query)
            
            # Favorites section with clickable items
            st.markdown('<div class="section-title">Favorites ▾</div>', unsafe_allow_html=True)
            
            # Create clickable buttons that look like text for favorite queries
            for query in config['favorite_queries']:
                if st.button(query, key=f"favorite_{query}", 
                            help="Click to ask this question",
                            use_container_width=True,
                            type="secondary"):
                    self.handle_query_click(query)

        # Add a "Deploy" button to the top right
        st.markdown('<div style="position: absolute; top: 5px; right: 10px; z-index: 1000;"><button style="background-color: transparent; color: white; border: none; cursor: pointer;">Deploy</button></div>', unsafe_allow_html=True)

        # Main content area with padding for fixed chat input
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Render the chat interface
        self.render_chat_interface()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add attachment icon to chat input
        st.markdown('<div class="attachment-icon">📎</div>', unsafe_allow_html=True)
            
        # Hide the buttons with CSS
        st.markdown("""
        <style>
        [data-testid="baseButton-secondary"] {
            background-color: transparent !important;
            color: #b0b0b0 !important;
            border: none !important;
            text-align: left !important;
            padding: 5px 0 !important;
            font-size: 14px !important;
        }
        
        [data-testid="baseButton-secondary"]:hover {
            color: white !important;
            text-decoration: underline !important;
            background-color: transparent !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_chat_interface(self):
        st.title(config['app_title'])
        st.markdown(f"<p class='app-description'>{config['app_description']}</p>", unsafe_allow_html=True)

        # Display chat history
        for message in st.session_state.history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Process pending query if there is one
        if st.session_state.pending_query:
            query = st.session_state.pending_query
            st.session_state.pending_query = None
            self.process_user_input(query)

        # Chat input (will be positioned at the bottom with CSS)
        if prompt := st.chat_input("Type a message"):
            self.process_user_input(prompt)
    
    def process_user_input(self, prompt):
        # Add user message to chat history
        st.session_state.history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate bot response
        response = self.generate_response(prompt)
        
        # Add bot response to chat history
        st.session_state.history.append({"role": "assistant", "content": response})
        
        # Display bot response
        with st.chat_message("assistant"):
            st.markdown(response)
    
    def generate_response(self, prompt):
        # Here you would connect to your actual AI model
        # For this example, we're using a simple pattern matching system
        
        model = st.session_state.model_name
        prompt_lower = prompt.lower()
        
        # Add the model name to the response to show it's being used
        model_info = f"*Using model: {model}*\n\n"
        
        if "symptom" in prompt_lower or "feel" in prompt_lower or "analyzer" in prompt_lower:
            return model_info + "Based on the symptoms you've described, it could be several conditions. However, I recommend consulting with a healthcare professional for an accurate diagnosis. Would you like me to provide some general information about these symptoms?"
        
        elif "medication" in prompt_lower or "drug" in prompt_lower:
            return model_info + "I can provide general information about medications, but for specific advice about dosage or interactions, please consult your doctor or pharmacist. What medication would you like to know more about?"
        
        elif "diabetes" in prompt_lower:
            return model_info + "Common symptoms of diabetes include:\n\n- Increased thirst\n- Frequent urination\n- Extreme hunger\n- Unexplained weight loss\n- Fatigue\n- Blurred vision\n- Slow-healing sores\n- Frequent infections\n\nIf you're experiencing these symptoms, it's important to consult with a healthcare provider for proper diagnosis and treatment."
        
        elif "blood test" in prompt_lower:
            return model_info + "Reading blood test results requires understanding various components:\n\n1. Complete Blood Count (CBC)\n2. Basic Metabolic Panel (BMP)\n3. Comprehensive Metabolic Panel (CMP)\n4. Lipid Panel\n5. Thyroid Function Tests\n\nWhich specific aspect of blood test results would you like me to explain?"
        
        elif "antibiotics" in prompt_lower:
            return model_info + "Common side effects of antibiotics may include:\n\n- Diarrhea\n- Nausea and vomiting\n- Stomach pain\n- Allergic reactions\n- Fungal infections\n\nThe severity and specific side effects vary depending on the type of antibiotic. If you're experiencing severe side effects, contact your healthcare provider immediately."
        
        elif "hypertension" in prompt_lower:
            return model_info + "Diet recommendations for hypertension (high blood pressure) include:\n\n1. Reduce sodium intake (less than 2,300mg daily)\n2. Follow the DASH diet (rich in fruits, vegetables, whole grains)\n3. Limit alcohol consumption\n4. Increase potassium intake (bananas, potatoes, spinach)\n5. Reduce caffeine consumption\n6. Maintain a healthy weight\n\nWould you like more specific information about any of these recommendations?"
        
        elif "burn" in prompt_lower:
            return model_info + "First aid for minor burns includes:\n\n1. Cool the burn with cool (not cold) running water for 10-15 minutes\n2. Don't apply ice directly to the burn\n3. Apply a gentle moisturizer or aloe vera gel\n4. Take over-the-counter pain relievers if needed\n5. Cover with a sterile, non-stick bandage\n\nSeek medical attention if the burn is larger than 3 inches, on the face/hands/genitals, or if it's deep/appears charred."
        
        elif "cholesterol" in prompt_lower:
            return model_info + "Understanding cholesterol levels:\n\n- Total cholesterol: Less than 200 mg/dL is desirable\n- LDL (bad) cholesterol: Less than 100 mg/dL is optimal\n- HDL (good) cholesterol: 60 mg/dL or higher is protective\n- Triglycerides: Less than 150 mg/dL is normal\n\nHigh cholesterol increases risk of heart disease and stroke. Would you like information about how to improve your cholesterol levels?"
        
        elif "back pain" in prompt_lower:
            return model_info + "Exercise routines for back pain relief include:\n\n1. Gentle stretching (cat-cow, child's pose)\n2. Core strengthening exercises (planks, bridges)\n3. Low-impact aerobic activities (walking, swimming)\n4. Yoga or Pilates\n5. Proper posture exercises\n\nStart slowly and stop if pain increases. Would you like a detailed description of any specific exercise?"
        
        elif "health record" in prompt_lower:
            return model_info + "Managing your health records effectively involves:\n\n1. Requesting copies of your medical records from healthcare providers\n2. Organizing records chronologically or by condition\n3. Maintaining a medication list\n4. Tracking vital health information (allergies, immunizations, surgeries)\n5. Using digital health record apps or patient portals\n6. Regularly updating your information\n\nWould you like specific recommendations for health record management tools?"
        
        elif "diet" in prompt_lower or "food" in prompt_lower or "nutrition" in prompt_lower:
            return model_info + "A balanced diet is important for overall health. For your specific needs, I'd recommend including plenty of fruits, vegetables, whole grains, and lean proteins. Would you like more specific dietary recommendations?"
        
        elif "exercise" in prompt_lower or "workout" in prompt_lower:
            return model_info + "Regular physical activity is beneficial for both physical and mental health. The general recommendation is at least 150 minutes of moderate-intensity activity per week. What type of exercise are you interested in?"
        
        else:
            return model_info + "Thank you for your question. As a medical assistant, I can provide general health information, but always consult with a healthcare professional for personalized medical advice. Is there anything specific you'd like to know more about?"

# Initialize and run the chatbot
if __name__ == "__main__":
    chatbot = MedicalChatbot()

# Run the app: streamlit run streamlit_app.py
