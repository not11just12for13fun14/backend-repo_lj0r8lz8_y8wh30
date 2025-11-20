"""
Database Schemas for SignifyLearn

Each Pydantic model represents a MongoDB collection. Collection name is the
lowercase of the class name.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# Core domain schemas

class Gesture(BaseModel):
    name: str = Field(..., description="Gesture display name")
    slug: str = Field(..., description="Unique slug for URL")
    category: str = Field(..., description="Category e.g., A-Z, Numbers, Basics")
    difficulty: str = Field("Pemula", description="Pemula | Menengah | Lanjut")
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")
    video_url: Optional[str] = Field(None, description="Demonstration video URL")
    steps: List[str] = Field(default_factory=list, description="Step-by-step guide")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    tags: List[str] = Field(default_factory=list)

class Module(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    cover: Optional[str] = None
    lessons: List[str] = Field(default_factory=list, description="List of lesson headings")
    difficulty: str = Field("Pemula")

class QuizQuestion(BaseModel):
    module_slug: str = Field(..., description="Related module")
    prompt: str
    media: Optional[str] = None
    options: List[str]
    answer_index: int = Field(..., ge=0)

class User(BaseModel):
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    points: int = 0
    level: int = 1
    streak: int = 0
    badges: List[str] = Field(default_factory=list)

class Favorite(BaseModel):
    user_email: EmailStr
    gesture_slug: str

class Progress(BaseModel):
    user_email: EmailStr
    module_slug: str
    completed_lessons: List[int] = Field(default_factory=list)
    updated_at: Optional[datetime] = None
