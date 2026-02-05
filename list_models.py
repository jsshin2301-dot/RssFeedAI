import google.generativeai as genai
import os
import toml

# Load API key from secrets.toml manually since we are running a standalone script
try:
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    print("Listing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
