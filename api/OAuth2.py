from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import uuid
from typing import Union
from sqlmodel import Session, select
from .models import Profile
from .database import get_session

load_dotenv()

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(user_id: Union[int, uuid.UUID], db: Session = Depends(get_session)) -> Profile:
    """Retrieve a user profile by user ID."""
    user = db.exec(select(Profile).where(Profile.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def authenticate_user(username: str, password: str, db: Session = Depends(get_session)) -> Profile:
    """Authenticate a user by username and password."""
    user = db.exec(select(Profile).where(Profile.username == username)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def get_current_user(token: str, db: Session = Depends(get_session)) -> Profile:
    """Get the current user from the JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.exec(select(Profile).where(Profile.id == user_id)).first()
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
