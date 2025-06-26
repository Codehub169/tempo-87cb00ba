from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import datetime
from fastapi.responses import StreamingResponse # Import StreamingResponse

from backend.app import crud, models
from backend.app.database import get_db
from backend.app.services.gemini_service import generate_gemini_response

router = APIRouter()

# Pydantic Schemas for request and response bodies

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    sender: str # 'user' or 'ai'

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    sender: str
    timestamp: datetime.datetime

    class Config:
        orm_mode = True # Enable ORM mode for Pydantic

class ConversationBase(BaseModel):
    system_prompt_used: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime.datetime
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True

class UserMessageRequest(BaseModel):
    message_content: str
    api_key: str # Add api_key field


@router.post(
    "/conversation",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Creates a new chat conversation with a specified system prompt."
)
async def create_new_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Endpoint to create a new conversation."""
    db_conversation = crud.create_conversation(
        db=db, system_prompt_used=conversation.system_prompt_used
    )
    return db_conversation


@router.get(
    "/conversation/{conversation_id}/messages",
    response_model=List[MessageResponse],
    summary="Get messages for a conversation",
    description="Retrieves all messages for a specific conversation ID."
)
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Endpoint to retrieve messages for a conversation."""
    messages = crud.get_messages_for_conversation(
        db=db, conversation_id=conversation_id, skip=skip, limit=limit
    )
    if not messages and not crud.get_conversation(db, conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return messages


@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    summary="Get all conversations",
    description="Retrieves a list of all conversations with their messages."
)
async def get_all_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Endpoint to retrieve all conversations."""
    conversations = crud.get_conversations(db, skip=skip, limit=limit)
    return conversations


@router.post(
    "/conversation/{conversation_id}/send_message",
    summary="Send a user message and get AI response (streaming)",
    description="Sends a user message to a conversation and streams the AI response.",
    response_model=None # We will return StreamingResponse directly
)
async def send_user_message_and_get_ai_response(
    conversation_id: int,
    user_message_req: UserMessageRequest,
    db: Session = Depends(get_db)
):
    """Endpoint to send a user message and receive an AI response."""
    db_conversation = crud.get_conversation(db, conversation_id);
    if not db_conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    # 1. Save user message
    crud.create_message(
        db=db, conversation_id=conversation_id, sender="user", content=user_message_req.message_content
    )

    # 2. Prepare chat history for AI model
    chat_history_messages = crud.get_messages_for_conversation(db, conversation_id)
    # The last message in chat_history_messages is the current user message, which should be passed as user_message.
    # The chat_history for the model should be everything *before* the current user message.
    chat_history_for_gemini = chat_history_messages[:-1] # Exclude the current user message

    async def generate_response_chunks():
        full_ai_response_content = ""
        async for chunk in generate_gemini_response(
            api_key=user_message_req.api_key,
            system_prompt=db_conversation.system_prompt_used,
            chat_history=chat_history_for_gemini,
            user_message=user_message_req.message_content
        ):
            full_ai_response_content += chunk
            yield chunk
        
        # 4. Save AI message after the stream is complete
        # We need a new DB session for this, as the original one might be closed by FastAPI's dependency.
        # However, for simplicity and given the context, we'll use a new session within this async generator if needed,
        # or rely on FastAPI's handling if the session remains open until the response is fully sent.
        # For now, let's assume the session from Depends is still valid or we pass a callable.
        # A more robust solution might involve a background task or a different way to commit the final message.
        # For this example, we'll pass the db session and ensure it's committed.
        
        # Re-get the db session to ensure it's active for the final save
        # This is a simplification; in a real-world scenario, you might use a background task
        # or a different approach to ensure the session is managed correctly after streaming.
        db_for_save = next(get_db())
        try:
            crud.create_message(
                db=db_for_save, conversation_id=conversation_id, sender="ai", content=full_ai_response_content
            )
            db_for_save.commit() # Ensure commit happens
        finally:
            db_for_save.close()


    return StreamingResponse(generate_response_chunks(), media_type="text/plain")


@router.delete(
    "/conversation/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
    description="Deletes a conversation and all its associated messages."
)
async def delete_existing_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Endpoint to delete a conversation."""
    if not crud.delete_conversation(db, conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return # No content to return for 204