
from fastapi import APIRouter, Depends, HTTPException
from ..models import StockData
from ..database import get_session
from api import screener
from sqlmodel import Session, select
router = APIRouter(
    prefix='/stock',
    tags=['Stock']
)
@router.get('/load_stock_data/')
def load_stock_data(db: Session = Depends(get_session)):
    """
    Load stock data from NSE and update the database.
    """
    try:
        screener.upload_stock_data(db)
        return {"message": "Stock data loaded successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while loading stock data.")

@router.put('/update_stock_data/')
def update_stock_data(db: Session = Depends(get_session)):
    """
    Update stock data in the database.
    """
    try:
        screener.upload_stock_data(db)
        return {"message": "Stock data updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while updating stock data.")
