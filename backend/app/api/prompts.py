from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import datetime

from backend.app import crud, models
from backend.app.database import get_db

router = APIRouter()

# Pydantic Schemas for request and response bodies for Prompts

class PromptBase(BaseModel):
    name: str
    content: str

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

class PromptResponse(PromptBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True # Enable ORM mode for Pydantic

@router.post(
    "/prompts",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new system prompt",
    description="Allows users to save a new custom system prompt."
)
async def create_new_prompt(
    prompt: PromptCreate,
    db: Session = Depends(get_db)
):
    """Endpoint to create a new prompt."""
    db_prompt = crud.get_prompt_by_name(db, name=prompt.name);
    if db_prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt with this name already exists.")
    return crud.create_prompt(db=db, name=prompt.name, content=prompt.content)

@router.get(
    "/prompts",
    response_model=List[PromptResponse],
    summary="Get all system prompts",
    description="Retrieves a list of all saved system prompts."
)
async def get_all_prompts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Endpoint to retrieve all prompts."""
    prompts = crud.get_prompts(db, skip=skip, limit=limit)
    return prompts

@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    summary="Get a system prompt by ID",
    description="Retrieves a single system prompt by its ID."
)
async def get_single_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Endpoint to retrieve a single prompt by ID."""
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found.")
    return db_prompt

@router.put(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    summary="Update an existing system prompt",
    description="Updates the name or content of an existing system prompt."
)
async def update_existing_prompt(
    prompt_id: int,
    prompt: PromptUpdate,
    db: Session = Depends(get_db)
):
    """Endpoint to update an existing prompt."""
    # Check if a prompt with the new name already exists (if name is being updated)
    if prompt.name:
        existing_prompt = crud.get_prompt_by_name(db, name=prompt.name)
        if existing_prompt and existing_prompt.id != prompt_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prompt with this name already exists.")

    db_prompt = crud.update_prompt(db, prompt_id=prompt_id, name=prompt.name, content=prompt.content)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found.")
    return db_prompt

@router.delete(
    "/prompts/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a system prompt",
    description="Deletes a system prompt by its ID."
)
async def delete_existing_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Endpoint to delete a prompt."""
    if not crud.delete_prompt(db, prompt_id=prompt_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found.")
    return # No content to return for 204
