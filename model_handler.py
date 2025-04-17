# model_handler.py (Model Interaction Layer)
from groq import Groq
import streamlit as st

class GroqModelHandler:
    def __init__(self, client):
        self.client = client
    
    def generate(self, prompt, model_name, temperature, max_tokens, stream=True):
        full_response = ""
        message_placeholder = st.empty()
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            return full_response
        
        except Exception as e:
            raise RuntimeError(f"Model Error: {str(e)}")