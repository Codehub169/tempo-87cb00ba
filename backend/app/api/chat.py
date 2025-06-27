from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import datetime

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
    liked: bool
    disliked: bool

    class Config:
        from_attributes = True # Enable ORM mode for Pydantic

class ConversationBase(BaseModel):
    system_prompt_used: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime.datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class UserMessageRequest(BaseModel):
    message_content: str
    api_key: str # Add api_key field

class MessageFeedbackRequest(BaseModel):
    liked: Optional[bool] = None
    disliked: Optional[bool] = None


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
    # First, check if conversation exists
    db_conversation = crud.get_conversation(db, conversation_id)
    if not db_conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = crud.get_messages_for_conversation(
        db=db, conversation_id=conversation_id, skip=skip, limit=limit
    )
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
    db_conversation = crud.get_conversation(db, conversation_id)
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
    try:
        ai_response_content = await generate_gemini_response(
            api_key=user_message_req.api_key, # Pass the API key
            system_prompt=db_conversation.system_prompt_used,
            chat_history=chat_history_for_gemini[:-1], # Pass history *before* current user message
            user_message=user_message_req.message_content
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # 4. Save AI message
    db_ai_message = crud.create_message(
        db=db, conversation_id=conversation_id, sender="ai", content=ai_response_content
    )

    return db_ai_message


@router.put(
    "/message/{message_id}/feedback",
    response_model=MessageResponse,
    summary="Add feedback to a message",
    description="Allows a user to like or dislike an AI message."
)
async def update_message_feedback_endpoint(
    message_id: int,
    feedback: MessageFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Endpoint to update message feedback."""
    db_message_check = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not db_message_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    if db_message_check.sender != 'ai':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feedback can only be provided for AI messages.")
    
    db_message = crud.update_message_feedback(
        db, message_id=message_id, liked=feedback.liked, disliked=feedback.disliked
    )
    if not db_message:
        # This case should ideally not be hit if the check above passes, but it's good practice
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found during update.")
    return db_message


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
