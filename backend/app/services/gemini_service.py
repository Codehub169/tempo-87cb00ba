from typing import List, Dict
import google.generativeai as genai
from backend.app.core.config import settings

async def generate_gemini_response(system_prompt: str, chat_history: List[Dict], user_message: str) -> str:
    """Generates an AI response using the Google Gemini API."""
    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Initialize the model with the system prompt
    # Using 'gemini-2.5-flash' as a general-purpose model, can be updated to newer models like 'gemini-1.5-pro-latest'
    # if system instruction support is confirmed for that specific model and API version.
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt
    )

    # Prepare chat history for the model
    # The Gemini API expects roles 'user' and 'model'. Map 'ai' from our DB to 'model'.
    # The chat_history passed from chat.py already has the 'parts' field as a list of content.
    gemini_history = []
    for msg in chat_history:
        role = 'user' if msg['role'] == 'user' else 'model'
        gemini_history.append({'role': role, 'parts': msg['parts']})

    # Start a chat session with the prepared history
    chat = model.start_chat(history=gemini_history)

    # Send the user's latest message and get the AI's response
    try:
        response = await chat.send_message_async(user_message)
        return response.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        # In a production environment, consider more robust error handling or logging.
        return "An error occurred while generating the AI response. Please try again later."
