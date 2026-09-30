"""Request validation models (Pydantic)."""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Level = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
Status = Literal["ACTIVE", "PAUSED", "COMPLETED"]
Category = Literal["Photography", "Music", "Coding", "Art", "Fitness", "Cooking", "Other"]
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,30}$")
    email: str = Field(pattern=EMAIL_RE, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str = Field(pattern=EMAIL_RE, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    bio: Optional[str] = Field(default=None, max_length=500)
    interests: Optional[str] = Field(default=None, max_length=300)
    is_public: Optional[bool] = None
    profile_picture_file_id: Optional[str] = None


class SkillIn(BaseModel):
    skill_name: str = Field(min_length=1, max_length=80)
    category: Category = "Other"
    current_level: Level = "BEGINNER"
    target_level: Level = "INTERMEDIATE"
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    status: Status = "ACTIVE"
    description: str = Field(default="", max_length=500)


class SkillUpdate(BaseModel):
    skill_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    category: Optional[Category] = None
    current_level: Optional[Level] = None
    target_level: Optional[Level] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    status: Optional[Status] = None
    description: Optional[str] = Field(default=None, max_length=500)


class PracticeIn(BaseModel):
    skill_id: str
    duration_minutes: int = Field(gt=0, le=1440)
    activity: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=1000)
    practiced_at: Optional[date] = None


class GoalIn(BaseModel):
    skill_id: str
    title: str = Field(min_length=1, max_length=120)
    target_value: float = Field(gt=0)
    unit: str = Field(default="hours", min_length=1, max_length=20)
    deadline: Optional[date] = None
    milestones: Optional[List[float]] = None  # e.g. [5, 10, 20, 30]; default 25/50/75/100 %


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    target_value: Optional[float] = Field(default=None, gt=0)
    current_value: Optional[float] = Field(default=None, ge=0)
    deadline: Optional[date] = None
    status: Optional[Status] = None


class PostIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    skill_id: Optional[str] = None
    milestone_id: Optional[str] = None
    file_id: Optional[str] = None


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class ReportIn(BaseModel):
    reason: str = Field(min_length=3, max_length=300)
