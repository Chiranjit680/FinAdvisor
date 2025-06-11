
from ..models import Profile, ProfileCreate, ProfileOut
from ..database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..utils import hash_password

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
