from google import genai
from google.genai import types
import streamlit as st
from src.prompt import system_instruction
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.genai.errors import ServerError


# Load Gemini API key from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not set in Streamlit Secrets.")


# Initialize Gemini client
client = genai.Client(api_key=api_key)

def convert_messages_to_gemini(messages):
    """
    Convert the existing OpenAI/Groq-style conversation
    into Gemini's conversation format.
    """

    history = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        # Gemini receives the system instruction separately.
        if role == "system":
            continue

        # Gemini uses "model" instead of "assistant".
        if role == "assistant":
            role = "model"

        if role in ["user", "model"]:
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=content)]
                )
            )

    return history


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ServerError),
    reraise=True
)
def order_request(messages, model="gemini-3.6-flash", temperature=0):
    """
    Send the complete conversation to Gemini and return
    the model's text response.
    """

    history = convert_messages_to_gemini(messages)

    response = client.models.generate_content(
        model=model,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature
        )
    )

    return response.text


# Initial conversation
messages = [
    {
        "role": "system",
        "content": system_instruction
    },
    {
        "role": "assistant",
        "content": (
            "How you dey! Welcome to DishDelivery Nigerian Restaurant! 🍽️\n\n"
            "I'm here to help you place your order for our authentic Nigerian cuisine.\n"
            "Let me show you our menu first, then you can tell me what you'd like to order!"
        )
    }
]
