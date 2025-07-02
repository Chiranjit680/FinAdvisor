from ..models import Profile, ProfileCreate, ProfileOut
from ..database import get_session
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select
from ..utils import hash_password
from ..OAuth2 import authenticate_user, get_current_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Create OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

router = APIRouter(
    prefix='/user',
    tags=['User']
)

@router.get('/all/')
async def get_profiles(db: Session = Depends(get_session)):
    users = db.exec(select(Profile)).all()  # Use SQLModel style instead of db.query()
    print(users)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return {"users": users}
    
@router.get('/profile/{user_id}', response_model=ProfileOut)
async def get_profile(user_id: int, db: Session = Depends(get_session)):
    user = db.exec(select(Profile).where(Profile.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

@router.post('/create_profile/', response_model=ProfileOut)
async def create_profile(profile_in: ProfileCreate, db: Session = Depends(get_session)):
    """
    create a new user profile.
    """
    try:
        existing_user = db.exec(select(Profile).where(Profile.username == profile_in.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="username already exists")

        # convert profilecreate → profile
        hashed_password = hash_password(profile_in.password)
        new_profile = Profile(
            username=profile_in.username,
            email=profile_in.email,
            password_hash=hashed_password,
            name=profile_in.name,
            age=profile_in.age
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " an error occurred while creating the user profile.")

# Add login endpoint to generate token
@router.post('/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    Authenticate user and return access token
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    
    # You'll need to implement this function in OAuth2.py
    from datetime import timedelta
    from ..OAuth2 import JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
    from jose import jwt
    from datetime import datetime
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expires = datetime.utcnow() + access_token_expires
    
    to_encode = {
        "sub": str(user.id),
        "exp": expires
    }
    
    access_token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }









    

@router.get('/me', response_model=ProfileOut)
async def read_users_me(current_user: Profile = Depends(get_current_user)):
    return current_user