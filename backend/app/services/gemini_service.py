from typing import List, Dict
import google.generativeai as genai

async def generate_gemini_response(api_key: str, system_prompt: str, chat_history: List[Dict], user_message: str) -> str:
    """Generates an AI response using the Google Gemini API."""
    try:
        genai.configure(api_key=api_key)

        # Initialize the model with the system prompt
        # Using 'gemini-1.5-flash' as a robust and fast model.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )

        # Prepare chat history for the model
        # The Gemini API expects roles 'user' and 'model'. Map 'ai' from our DB to 'model'.
        gemini_history = []
        for msg in chat_history:
            role = 'user' if msg['role'] == 'user' else 'model'
            gemini_history.append({'role': role, 'parts': msg['parts']})

        # Start a chat session with the prepared history
        chat = model.start_chat(history=gemini_history)

        # Send the user's latest message and get the AI's response
        response = await chat.send_message_async(user_message)
        return response.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        # Raise an exception that can be caught by the API endpoint and returned as a proper HTTP error
        raise Exception(f"Failed to generate AI response. Please check your API key and network connection. Details: {e}")
