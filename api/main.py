
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Profile,Chat, Portfolio
from google import genai
import uuid


from dotenv import load_dotenv
import os
import yfinance as yf
from nselib import capital_market
from .middlewares import RateLimitMiddleware
from sqlalchemy.exc import SQLAlchemyError
import logging
from api.database import engine

load_dotenv()

app = FastAPI()
import api.screener as screener
app.add_middleware(RateLimitMiddleware)
logger=logging.getLogger(__name__)

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

@app.get('/users/')
async def get_profiles(db: Session = Depends(get_session)):
    users = db.exec(select(Profile)).all()  # Use SQLModel style instead of db.query()
    print(users)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return {"users": users}

@app.post('/create_profile/')  # Removed response_model=Profile since you're returning a dict
async def create_profile(profile: Profile, db: Session = Depends(get_session)):
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return {"message": "Profile created successfully!", "profile": profile}

@app.get('/profile/{user_id}')
async def get_profile(user_id: int, db: Session = Depends(get_session)):
    user = db.exec(select(Profile).where(Profile.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

@app.post('/add_portfolio/{user_id}')
async def add_portfolio(user_id: uuid.UUID, portfolio: Portfolio, db: Session = Depends(get_session)):
    existing_portfolio = db.exec(select(Portfolio).where(Portfolio.user_id == user_id)).first()
    if existing_portfolio:
        raise HTTPException(status_code=400, detail="Portfolio already exists for this user")
    portfolio.user_id = user_id  # Set the user_id for the portfolio
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return {"message": "Portfolio added successfully!", "portfolio": portfolio}



client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# response = client.models.generate_content(
#     model="gemini-2.0-flash",
#     contents="Explain how AI works in a few words",
# )

# print(response.text)

@app.post('/chat_gemini/{user_id}')
async def chat_with_gemini(user_id: uuid.UUID, prompt: str, db: Session = Depends(get_session)):
    try:
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        if len(prompt) > 1000:
            raise HTTPException(status_code=400, detail="Prompt is too long. Please limit to 1000 characters.")
        hstr= db.exec(select(Chat).where(Chat.user_id==user_id)).all()
        history = ""
        for chat in hstr:
            history += "User:"+chat.human_message + " AI: " + chat.ai_message
        user_info = db.exec(select(Profile).where(Profile.id==user_id)).first()
        portfolio = db.exec(select(Portfolio).where(Portfolio.user_id==user_id)).first()
        username = user_info.username if user_info else "Unknown User"
        age= user_info.age if user_info else "Unknown Age"
        equity_amt = portfolio.equity_amt if portfolio else "Unknown Equity Amount"
        cash_amt = portfolio.cash_amt if portfolio else "Unknown Cash Amount"
        fd_amt = portfolio.fd_amt if portfolio else "Unknown FD Amount"
        debt_amt = portfolio.debt_amt if portfolio else "Unknown Debt Amount"
        real_estate_amt = portfolio.real_estate_amt if portfolio else "Unknown Real Estate Amount"
        bonds_amt = portfolio.bonds_amt if portfolio else "Unknown Bonds Amount"
        crypto_amt = portfolio.crypto_amt if portfolio else "Unknown Crypto Amount"

        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
        context = f"""Context: {history}
You are a financial advisor. Answer the question based on the context provided and the user data.

User Data:
- User: {username}
- Age: {age}
- Equity Amount: {equity_amt}
- Cash Amount: {cash_amt}
- FD Amount: {fd_amt}
- Debt Amount: {debt_amt}
- Real Estate Amount: {real_estate_amt}
- Bonds Amount: {bonds_amt}
- Crypto Amount: {crypto_amt}

Take the user's financial situation, goals and age into account when responding.

User Question: {prompt}"""
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=context,
        )
        
       
        
        return {"response": response.text}
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e)+ " An error occurred while communicating with the Gemini API.")
 
@app.get('/stock_query/{user_id}/{symbol}') 
async def stock_query(user_id: uuid.UUID, symbol: str, query:str,db: Session = Depends(get_session)):
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")
        if len(symbol) >10:
            raise HTTPException(status_code=400, detail="Symbol is too long. Please limit to 10 characters.")
        stock=yf.Ticker(symbol)
        stock_info = stock.info 
        # Call Gemini API
        context="This is the data of the stock is user querying for: " + str(stock_info) +"use this to answer the user's query. Query:"+query
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=context
        )
        print(stock_info)
        
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while processing the stock query.")
@app.post('/load_stock_data/')
def load_stock_data(db: Session = Depends(get_session)):
    """
    Load stock data from NSE and update the database.
    """
    try:
        screener.upload_stock_data(db)
        return {"message": "Stock data loaded successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while loading stock data.")
@app.put('/update_stock_data/')
def update_stock_data(db: Session = Depends(get_session)):
    """
    Update stock data in the database.
    """
    try:
        screener.upload_stock_data(db)
        return {"message": "Stock data updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while updating stock data.")
