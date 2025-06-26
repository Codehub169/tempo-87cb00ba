from typing import List, Dict, AsyncGenerator
import google.generativeai as genai

async def generate_gemini_response(api_key: str, system_prompt: str, chat_history: List[Dict], user_message: str) -> AsyncGenerator[str, None]:
    """Generates an AI response using the Google Gemini API, streaming the response."""
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_prompt
    )

    gemini_history = []
    for msg in chat_history:
        # Corrected: Access attributes using dot notation, not dictionary keys
        role = 'user' if msg.sender == 'user' else 'model'
        gemini_history.append({'role': role, 'parts': [msg.content]}) # Ensure content is in a list for parts

    try:
        # Start a chat session with the prepared history
        chat = model.start_chat(history=gemini_history)

        # Send the user's latest message and stream the AI's response
        response_stream = await chat.send_message_async(user_message, stream=True)
        
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        yield "An error occurred while generating the AI response. Please try again later."