from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workout_entries = relationship(
        "WorkoutEntry", back_populates="user", cascade="all, delete-orphan"
    )
    exercises = relationship(
        "Exercise", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Exercise(Base):
    """Exercise catalog model that users can pick from"""
    __tablename__ = "exercises"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", name="uq_exercises_owner_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), index=True, nullable=False)
    category = Column(String(80), nullable=False)
    is_weighted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="exercises")


    workout_entries = relationship("WorkoutEntry", back_populates="exercise")

    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', weighted={self.is_weighted})>"


class WorkoutEntry(Base):
    """Workout log entry model with reps or duration and optional weight"""
    __tablename__ = "workout_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)
    workout_title = Column(String(120), nullable=False, index=True)
    reps = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    user = relationship("User", back_populates="workout_entries")
    exercise = relationship("Exercise", back_populates="workout_entries")

    def __repr__(self):
        return (
            f"<WorkoutEntry(id={self.id}, user_id={self.user_id}, exercise_id={self.exercise_id}, "
            f"reps={self.reps}, duration={self.duration_minutes}, weight={self.weight_kg})>"
        )
