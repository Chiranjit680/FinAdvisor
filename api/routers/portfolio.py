import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..models import Portfolio, Profile
from ..database import get_session
from ..OAuth2 import get_current_user
from fastapi.security import OAuth2PasswordBearer

# Create OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

router = APIRouter(
    prefix='/portfolio',
    tags=['Portfolio']
)

# Original route - kept for backward compatibility
@router.post('/add_portfolio/{user_id}')
async def add_portfolio(user_id: uuid.UUID, portfolio: Portfolio, db: Session = Depends(get_session)):
    existing_portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
    if existing_portfolio:
        raise HTTPException(status_code=400, detail="Portfolio already exists for this user")
    portfolio.user_id = user_id  # Set the user_id for the portfolio
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {"message": "Portfolio added successfully!", "portfolio": portfolio}

# New secured route using OAuth2
@router.post('/secure/add_portfolio')
async def add_secure_portfolio(
    portfolio: Portfolio, 
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    """
    Add portfolio for the authenticated user
    """
    current_user = get_current_user(token, db)
    
    existing_portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == current_user.id)).first()
    if existing_portfolio:
        raise HTTPException(status_code=400, detail="Portfolio already exists for this user")
    
    portfolio.user_id = current_user.id  # Set the user_id to the authenticated user
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {"message": "Portfolio added successfully!", "portfolio": portfolio}

# Original route - kept for backward compatibility
@router.get('/portfolio/{user_id}')
async def get_portfolio(user_id: uuid.UUID, db: Session = Depends(get_session)):
    portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this user")
    return {"portfolio": portfolio}

# New secured route using OAuth2
@router.get('/secure/my_portfolio')
async def get_secure_portfolio(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    """
    Get portfolio for the authenticated user
    """
    # Get the current user from the token
    current_user = get_current_user(token, db)
    
    print(f"Fetching portfolio for user: {current_user.username}")
    portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == current_user.id)).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this user")
    
    return portfolio

# Update portfolio (new secured endpoint)
@router.put('/secure/update_portfolio')
async def update_secure_portfolio(
    portfolio_update: Portfolio,
    current_user: Profile = Depends(lambda token: get_current_user(token, Depends(get_session))),
    db: Session = Depends(get_session)
):
    """
    Update portfolio for the authenticated user
    """
    existing_portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == current_user.id)).first()
    if not existing_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this user")
    
    # Update portfolio fields
    for field, value in portfolio_update.dict(exclude_unset=True, exclude={'id', 'user_id'}).items():
        setattr(existing_portfolio, field, value)
    
    db.add(existing_portfolio)
    db.commit()
    db.refresh(existing_portfolio)
    return {"message": "Portfolio updated successfully!", "portfolio": existing_portfolio}
