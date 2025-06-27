from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base

# Prompt Model
# Represents a saved system prompt that a user can configure and reuse.
class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True) # Unique ID for the prompt
    name = Column(String, unique=True, index=True, nullable=False) # Name of the prompt, must be unique
    content = Column(Text, nullable=False) # The actual system prompt text
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp of creation

    # Relationship to Conversations (optional, for tracking which conversations used this prompt)
    # conversations = relationship("Conversation", back_populates="prompt_ref")

# Conversation Model
# Represents a single chat session between the user and the AI.
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True) # Unique ID for the conversation
    system_prompt_used = Column(Text, nullable=False) # The system prompt active for this conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp of creation

    # Relationship to Messages: A conversation can have many messages.
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# Message Model
# Represents a single message within a conversation, either from the user or the AI.
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True) # Unique ID for the message
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False) # Foreign key to the parent conversation
    sender = Column(String, nullable=False) # 'user' or 'ai'
    content = Column(Text, nullable=False) # The message content
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) # Timestamp of message creation
    liked = Column(Boolean, default=False) # New field for like status
    disliked = Column(Boolean, default=False) # New field for dislike status

    # Relationship to Conversation: A message belongs to one conversation.
    conversation = relationship("Conversation", back_populates="messages")