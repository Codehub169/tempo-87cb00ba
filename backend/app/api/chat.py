from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import datetime # Import datetime

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


@router.post(
    "/conversation/{conversation_id}/send_message",
    response_model=MessageResponse,
    summary="Send a user message and get AI response",
    description="Sends a user message to a conversation and generates an AI response. Returns the AI's message."
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
    chat_history_for_gemini = [
        {"role": msg.sender, "parts": [msg.content]}
        for msg in chat_history_messages
    ]

    # 3. Get AI response
    # The last message in chat_history_for_gemini is the current user message, which should be passed as user_message.
    # The chat_history for the model should be everything *before* the current user message.
    ai_response_content = await generate_gemini_response(
        api_key=user_message_req.api_key, # Pass the API key
        system_prompt=db_conversation.system_prompt_used,
        chat_history=chat_history_for_gemini[:-1], # Pass history *before* current user message
        user_message=user_message_req.message_content
    )

    # 4. Save AI message
    db_ai_message = crud.create_message(
        db=db, conversation_id=conversation_id, sender="ai", content=ai_response_content
    )

    return db_ai_message


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
