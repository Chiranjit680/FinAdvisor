import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..models import Portfolio
from ..database import get_session
router = APIRouter(
    prefix='/portfolio',
    tags=['Portfolio']
)

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

@router.get('/portfolio/{user_id}')
async def get_portfolio(user_id: uuid.UUID, db: Session = Depends(get_session)):
    portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this user")
    return {"portfolio": portfolio}
