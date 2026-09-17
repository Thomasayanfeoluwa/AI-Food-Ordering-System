from google import genai
from google.genai import types
from src.prompt import system_instruction
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Load Gemini API key
api_key = st.secrets.get("GEMINI_API_KEY")

st.write("API key loaded:", "Yes" if api_key else "No")

if not api_key:
    raise ValueError("GEMINI_API_KEY not set.")

# Initialize Gemini client
client = genai.Client(api_key=api_key)


def order_request(messages, model="gemini-3.8-flash", temperature=0):
    response = client.models.generate_content(
        model=model,
        contents=messages,
        config=types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction
        )
    )

    return response.text
