from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select    
from ..models import UserLogin,Profile
from ..database import get_session
from ..utils import verify_password, generate_jwt_token
router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)

@router.post('/login', response_model=UserLogin)
async def login(user_login: UserLogin, db: Session = Depends(get_session)):
    user = db.exec(select(Profile).where(Profile.username == user_login.username)).first()

    if not user or not verify_password(user_login.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = generate_jwt_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}
