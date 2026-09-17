from groq import Groq
from src.prompt import system_instruction
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# api_key = os.environ.get("GROQ_API_KEY")
api_key = st.secrets.get("GROQ_API_KEY")


st.write("API key loaded:", "Yes" if api_key else "No")

if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

client = Groq(api_key=api_key)


# Initialize LLM
# messages = [
#     {"role": "system", "content": system_instruction}
# ]

# def order_request(messages, model="openai/gpt-oss-120b", temperature=0):
# #  model="llama-3.3-70b-versatile"
#     response = client.chat.completions.create(
#         model=model,
#         messages=messages,
#         temperature=temperature
#     )
#     return response.choices[0].message.content


def order_request(messages, model="openai/gpt-oss-120b", temperature=0):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"Groq API Error: {type(e).__name__}")
        st.error(str(e))
        raise


