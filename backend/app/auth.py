import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
	raise RuntimeError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
	expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
	payload = {"sub": subject, "exp": expire}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, username: str, password: str):
	user = db.query(models.User).filter(models.User.username == username).first()
	if not user:
		return None
	if not verify_password(password, user.hashed_password):
		return None
	return user


def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: Session = Depends(get_db),
) -> models.User:
	token = credentials.credentials
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid authentication credentials",
	)

	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if not username:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	user = db.query(models.User).filter(models.User.username == username).first()
	if not user:
		raise credentials_exception
	return user
