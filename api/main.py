
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Profile,Chat, Portfolio, ProfileCreate, ProfileOut
from google import genai
import uuid
from api.utils import hash_password

from api.routers import user, chat, portfolio, stock
from dotenv import load_dotenv
import os
import yfinance as yf

from .middlewares import RateLimitMiddleware, AuthMiddleware, LoggerMiddleware
from sqlalchemy.exc import SQLAlchemyError
import logging
from api.database import engine

load_dotenv()

app = FastAPI()
import api.screener as screener
from api import routers
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggerMiddleware)
logger=logging.getLogger(__name__)

app.include_router(user.router)
app.include_router(chat.router)
app.include_router(portfolio.router)
app.include_router(stock.router)

@app.on_event("startup")
def on_startup():
    """
    Startup event handler with improved error handling and logging.
    """
    try:
        logger.info("Application startup initiated")
        
        # Create database tables
        create_db_and_tables()
        logger.info("Database tables created successfully")
        
        # Get database session
        try:
            with Session(engine) as session:

                # Upload stock data in background to avoid blocking startup
                logger.info("Starting stock data upload...")
                result = screener.upload_stock_data(session)
                if result["success"]:
                    logger.info(f"Stock data upload completed: {result['message']}")
                else:
                    logger.error(f"Stock data upload failed: {result['message']}")
        except SQLAlchemyError as e:
            logger.error(f"Database error during startup: {str(e)}")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Don't raise the exception to prevent app from failing to start
        # You might want to set a flag to indicate incomplete initialization


@app.get("/")
async def root():
    return {"message": "Welcome to the FinAdvisor API!"}



