from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExerciseBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    is_weighted: bool = False


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    category: Optional[str] = Field(default=None, min_length=2, max_length=80)
    is_weighted: Optional[bool] = None


class ExerciseRead(ExerciseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkoutEntryBase(BaseModel):
    workout_title: str = Field(min_length=2, max_length=120)
    exercise_id: int = Field(gt=0)
    reps: Optional[int] = Field(default=None, gt=0, le=1000)
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    weight_kg: Optional[float] = Field(default=None, ge=0, le=500)
    performed_at: Optional[datetime] = None


class WorkoutEntryCreate(WorkoutEntryBase):
    pass


class WorkoutEntryUpdate(BaseModel):
    workout_title: Optional[str] = Field(default=None, min_length=2, max_length=120)
    exercise_id: Optional[int] = Field(default=None, gt=0)
    reps: Optional[int] = Field(default=None, gt=0, le=1000)
    duration_minutes: Optional[int] = Field(default=None, gt=0, le=600)
    weight_kg: Optional[float] = Field(default=None, ge=0, le=500)
    performed_at: Optional[datetime] = None


class WorkoutEntryRead(WorkoutEntryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
