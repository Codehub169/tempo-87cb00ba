from sqlalchemy.orm import Session
import datetime

from backend.app.models import Prompt, Conversation, Message

# CRUD operations for Prompts

def create_prompt(db: Session, name: str, content: str):
    """Creates a new prompt in the database."""
    db_prompt = Prompt(name=name, content=content)
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def get_prompt(db: Session, prompt_id: int):
    """Retrieves a single prompt by its ID."""
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()

def get_prompt_by_name(db: Session, name: str):
    """Retrieves a single prompt by its name."""
    return db.query(Prompt).filter(Prompt.name == name).first()

def get_prompts(db: Session, skip: int = 0, limit: int = 100):
    """Retrieves a list of prompts with pagination."""
    return db.query(Prompt).offset(skip).limit(limit).all()

def update_prompt(db: Session, prompt_id: int, name: str = None, content: str = None):
    """Updates an existing prompt. Returns the updated prompt or None if not found."""
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt:
        if name is not None: 
            db_prompt.name = name
        if content is not None: 
            db_prompt.content = content
        db.commit()
        db.refresh(db_prompt)
    return db_prompt

def delete_prompt(db: Session, prompt_id: int):
    """Deletes a prompt by its ID. Returns True if deleted, False otherwise."""
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if db_prompt:
        db.delete(db_prompt)
        db.commit()
        return True
    return False

# CRUD operations for Conversations

def create_conversation(db: Session, system_prompt_used: str):
    """Creates a new conversation in the database."""
    db_conversation = Conversation(system_prompt_used=system_prompt_used)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def get_conversation(db: Session, conversation_id: int):
    """Retrieves a single conversation by its ID."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def get_conversations(db: Session, skip: int = 0, limit: int = 100):
    """Retrieves a list of conversations with pagination."""
    return db.query(Conversation).offset(skip).limit(limit).all()

def delete_conversation(db: Session, conversation_id: int):
    """Deletes a conversation by its ID. Returns True if deleted, False otherwise."""
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
        return True
    return False

# CRUD operations for Messages

def create_message(db: Session, conversation_id: int, sender: str, content: str):
    """Creates a new message in the database for a given conversation."""
    db_message = Message(conversation_id=conversation_id, sender=sender, content=content)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_for_conversation(db: Session, conversation_id: int, skip: int = 0, limit: int = 100):
    """Retrieves messages for a specific conversation with pagination."""
    return db.query(Message).filter(Message.conversation_id == conversation_id).offset(skip).limit(limit).all()

def update_message_feedback(db: Session, message_id: int, liked: bool = None, disliked: bool = None):
    """Updates the liked/disliked status of a message."""
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if db_message:
        if liked is not None:
            db_message.liked = liked
            if liked: # If liked, ensure not disliked
                db_message.disliked = False
        if disliked is not None:
            db_message.disliked = disliked
            if disliked: # If disliked, ensure not liked
                db_message.liked = False
        db.commit()
        db.refresh(db_message)
    return db_message