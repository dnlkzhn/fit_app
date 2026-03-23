from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from datetime import datetime
from .database import get_db, engine, Base
from . import models
from . import schemas
from . import auth

# Initialize FastAPI app
app = FastAPI(
    title="Cloud WebApp API",
    version="1.0.0",
    description="Multi-tier web application with authentication and CRUD operations"
)


@app.on_event("startup")
def initialize_database_on_startup():
    """Auto-create database tables on startup"""
    Base.metadata.create_all(bind=engine)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_workout_input(exercise: models.Exercise, reps, duration_minutes, weight_kg):
    if exercise.is_weighted:
        if reps is None:
            raise HTTPException(status_code=422, detail="reps is required for weighted exercises")
        if duration_minutes is not None:
            raise HTTPException(status_code=422, detail="duration_minutes must be omitted for weighted exercises")
        if weight_kg is None:
            raise HTTPException(status_code=422, detail="weight_kg is required for weighted exercises")
    else:
        if duration_minutes is None:
            raise HTTPException(status_code=422, detail="duration_minutes is required for non-weighted exercises")
        if reps is not None:
            raise HTTPException(status_code=422, detail="reps must be omitted for non-weighted exercises")
        if weight_kg is not None:
            raise HTTPException(status_code=422, detail="weight_kg must be omitted for non-weighted exercises")


def get_default_exercises():
    return [
        {"name": "Barbell Squat", "category": "Legs", "is_weighted": True},
        {"name": "Bench Press", "category": "Chest", "is_weighted": True},
        {"name": "Deadlift", "category": "Back", "is_weighted": True},
        {"name": "Overhead Press", "category": "Shoulders", "is_weighted": True},
        {"name": "Plank", "category": "Core", "is_weighted": False},
        {"name": "Push-up", "category": "Chest", "is_weighted": False},
        {"name": "Running", "category": "Cardio", "is_weighted": False},
    ]


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to Cloud WebApp API",
        "docs": "/docs",
        "health": "/health",
        "database": "/health/db",
        "init_db": "/init-db",
        "tables": "/tables",
        "register": "/register",
        "login": "/login",
        "me": "/me",
        "exercises": "/exercises",
        "seed_exercises": "/seed-exercises",
        "workout_entries": "/workout-entries"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "backend"
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    """Database connectivity health check"""
    try:
        result = db.execute(text("SELECT 1")).scalar()
        version = db.execute(text("SELECT version()")).scalar()

        return {
            "status": "healthy",
            "service": "database",
            "connection": "successful",
            "test_query_result": result,
            "postgres_version": version.split(",")[0] if version else "unknown"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )


@app.post("/init-db")
def initialize_database():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        return {
            "status": "success",
            "message": "Database tables created successfully",
            "tables": tables
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tables: {str(e)}"
        )


@app.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    """List all tables in the database"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        table_info = {}
        for table in tables:
            columns = inspector.get_columns(table)
            table_info[table] = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"]
                }
                for col in columns
            ]

        return {
            "status": "success",
            "table_count": len(tables),
            "tables": table_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tables: {str(e)}"
        )


@app.get("/exercises", response_model=list[schemas.ExerciseRead])
def list_exercises(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """List all available exercises users can pick from"""
    return (
        db.query(models.Exercise)
        .filter(models.Exercise.owner_user_id == current_user.id)
        .order_by(models.Exercise.name.asc())
        .all()
    )


@app.post("/exercises", response_model=schemas.ExerciseRead, status_code=201)
def create_exercise(
    payload: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Create a new exercise in the catalog"""
    existing = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.owner_user_id == current_user.id,
            models.Exercise.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Exercise with this name already exists")

    exercise = models.Exercise(
        owner_user_id=current_user.id,
        name=payload.name,
        category=payload.category,
        is_weighted=payload.is_weighted,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@app.patch("/exercises/{exercise_id}", response_model=schemas.ExerciseRead)
def update_exercise(
    exercise_id: int,
    payload: schemas.ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Update an exercise in the catalog"""
    exercise = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.id == exercise_id,
            models.Exercise.owner_user_id == current_user.id,
        )
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    if payload.name and payload.name != exercise.name:
        existing = (
            db.query(models.Exercise)
            .filter(
                models.Exercise.owner_user_id == current_user.id,
                models.Exercise.name == payload.name,
                models.Exercise.id != exercise.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Exercise with this name already exists")

    if payload.is_weighted is not None and payload.is_weighted != exercise.is_weighted:
        has_entries = (
            db.query(models.WorkoutEntry)
            .filter(models.WorkoutEntry.exercise_id == exercise.id)
            .first()
        )
        if has_entries:
            raise HTTPException(
                status_code=409,
                detail="Cannot change exercise type while workout entries exist",
            )

    if payload.name is not None:
        exercise.name = payload.name
    if payload.category is not None:
        exercise.category = payload.category
    if payload.is_weighted is not None:
        exercise.is_weighted = payload.is_weighted

    db.commit()
    db.refresh(exercise)
    return exercise


@app.delete("/exercises/{exercise_id}")
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Delete an exercise from the catalog"""
    exercise = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.id == exercise_id,
            models.Exercise.owner_user_id == current_user.id,
        )
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    has_entries = (
        db.query(models.WorkoutEntry)
        .filter(models.WorkoutEntry.exercise_id == exercise.id)
        .first()
    )
    if has_entries:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete exercise while workout entries exist",
        )

    db.delete(exercise)
    db.commit()
    return {"status": "success", "message": "Exercise deleted"}


@app.post("/register", response_model=schemas.UserRead, status_code=201)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new user with hashed password"""
    username_exists = db.query(models.User).filter(models.User.username == payload.username).first()
    if username_exists:
        raise HTTPException(status_code=409, detail="Username already exists")

    email_exists = db.query(models.User).filter(models.User.email == payload.email).first()
    if email_exists:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = auth.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = auth.create_access_token(subject=user.username)
    return schemas.Token(access_token=access_token)


@app.get("/me", response_model=schemas.UserRead)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Return the authenticated user"""
    return current_user


@app.post("/seed-exercises")
def seed_exercises(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Seed default exercise catalog for easier testing"""
    created = []
    for exercise_data in get_default_exercises():
        exists = (
            db.query(models.Exercise)
            .filter(
                models.Exercise.owner_user_id == current_user.id,
                models.Exercise.name == exercise_data["name"],
            )
            .first()
        )
        if exists:
            continue
        exercise = models.Exercise(owner_user_id=current_user.id, **exercise_data)
        db.add(exercise)
        created.append(exercise_data["name"])

    db.commit()

    return {
        "status": "success",
        "created_count": len(created),
        "created_exercises": created,
    }


@app.post("/workout-entries", response_model=schemas.WorkoutEntryRead, status_code=201)
def create_workout_entry(
    payload: schemas.WorkoutEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Persist workout entry for the authenticated user"""
    exercise = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.id == payload.exercise_id,
            models.Exercise.owner_user_id == current_user.id,
        )
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    validate_workout_input(
        exercise=exercise,
        reps=payload.reps,
        duration_minutes=payload.duration_minutes,
        weight_kg=payload.weight_kg,
    )

    workout_entry = models.WorkoutEntry(
        user_id=current_user.id,
        exercise_id=payload.exercise_id,
        workout_title=payload.workout_title,
        reps=payload.reps,
        duration_minutes=payload.duration_minutes,
        weight_kg=payload.weight_kg,
        performed_at=payload.performed_at or datetime.utcnow(),
    )
    db.add(workout_entry)
    db.commit()
    db.refresh(workout_entry)
    return workout_entry


@app.get("/workout-entries", response_model=list[schemas.WorkoutEntryRead])
def list_workout_entries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """List workout entries for authenticated user"""
    return (
        db.query(models.WorkoutEntry)
        .filter(models.WorkoutEntry.user_id == current_user.id)
        .order_by(models.WorkoutEntry.performed_at.desc())
        .all()
    )


@app.get("/workout-entries/{entry_id}", response_model=schemas.WorkoutEntryRead)
def get_workout_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Get a single workout entry owned by the authenticated user"""
    entry = (
        db.query(models.WorkoutEntry)
        .filter(
            models.WorkoutEntry.id == entry_id,
            models.WorkoutEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Workout entry not found")
    return entry


@app.patch("/workout-entries/{entry_id}", response_model=schemas.WorkoutEntryRead)
def update_workout_entry_patch(
    entry_id: int,
    payload: schemas.WorkoutEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Partially update a workout entry owned by the authenticated user"""
    entry = (
        db.query(models.WorkoutEntry)
        .filter(
            models.WorkoutEntry.id == entry_id,
            models.WorkoutEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Workout entry not found")

    next_exercise_id = payload.exercise_id if payload.exercise_id is not None else entry.exercise_id
    next_reps = payload.reps if payload.reps is not None else entry.reps
    next_duration = payload.duration_minutes if payload.duration_minutes is not None else entry.duration_minutes
    next_weight = payload.weight_kg if payload.weight_kg is not None else entry.weight_kg

    exercise = (
        db.query(models.Exercise)
        .filter(
            models.Exercise.id == next_exercise_id,
            models.Exercise.owner_user_id == current_user.id,
        )
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    validate_workout_input(
        exercise=exercise,
        reps=next_reps,
        duration_minutes=next_duration,
        weight_kg=next_weight,
    )

    if payload.exercise_id is not None:
        entry.exercise_id = payload.exercise_id
    if payload.workout_title is not None:
        entry.workout_title = payload.workout_title
    if payload.reps is not None:
        entry.reps = payload.reps
    if payload.duration_minutes is not None:
        entry.duration_minutes = payload.duration_minutes
    if payload.weight_kg is not None:
        entry.weight_kg = payload.weight_kg
    if payload.performed_at is not None:
        entry.performed_at = payload.performed_at

    db.commit()
    db.refresh(entry)
    return entry


@app.delete("/workout-entries/{entry_id}")
def delete_workout_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Delete a workout entry owned by the authenticated user"""
    entry = (
        db.query(models.WorkoutEntry)
        .filter(
            models.WorkoutEntry.id == entry_id,
            models.WorkoutEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Workout entry not found")

    db.delete(entry)
    db.commit()
    return {"status": "success", "message": "Workout entry deleted"}
