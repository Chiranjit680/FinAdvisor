from ..models import Chat, Profile, Portfolio
from ..database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette.requests import Request
import uuid
import yfinance as yf
from ..utils import chat_with_gemini, get_ticker_by_company, generate_sql_query, get_company_list, extract_company_ticker
from dotenv import load_dotenv
from datetime import date, timedelta
import os
import finnhub
from ..bertmodel_loader import tokenizer, model
from ..OAuth2 import get_current_user, authenticate_user, verify_password
from fastapi.security import OAuth2PasswordBearer

# Create OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")

load_dotenv()
finhub_api_key=os.getenv("FINHUB")
router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

finnhub_client = finnhub.Client(api_key=finhub_api_key)
def fetch_news(ticker:str)->str:
    date_today= str(date.today())
    date_past=str(date.today()-timedelta(days=90))
    news = finnhub_client.company_news(ticker, _from=date_past, to=date_today)
    return news

def financial_advice(user_id: uuid.UUID, prompt: str, db: Session = Depends(get_session)):
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
        response = chat_with_gemini(context)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get a response from the Gemini API.")

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)+ " An error occurred while communicating with the Gemini API.")

# Add an authenticated route that uses the OAuth2 system
@router.post("/secure-advice")
async def get_secure_financial_advice(
    request: Request,  # Use Request to access JSON body
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    """
    Get financial advice as an authenticated user
    """
    # Get current user from token
    current_user = get_current_user(token, db)
    
    # Extract prompt from request body
    body = await request.json()
    prompt = body.get("prompt")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    # Get advice using the financial_advice function
    response = financial_advice(current_user.id, prompt, db)
    
    # Save the chat to database
    new_chat = Chat(
        user_id=current_user.id,
        human_message=prompt,
        ai_message=response["response"]
    )
    
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    return response

# Update company_query to use authentication if needed
def company_query(user_id: uuid.UUID, request: Request, db: Session = Depends(get_session)):
   try:
       prompt = request.query_params.get("prompt")
       if not prompt:
           raise HTTPException(status_code=400, detail="Prompt cannot be empty")
       if len(prompt) > 1000:
             raise HTTPException(status_code=400, detail="Prompt is too long. Please limit to 1000 characters.")
       ticker=extract_company_ticker(prompt=prompt)
       sql_query=generate_sql_query(prompt=prompt, ticker=ticker)
       if not sql_query:
           raise HTTPException(status_code=500, detail="Failed to generate SQL query.")
       data = db.exec(sql_query).first()
       context= f"This is the information about the company from the database about which the user might have asked read the question {prompt} and use the data: {data} as context"
       response=chat_with_gemini(context)
       return response
   except Exception as e:
       raise HTTPException(status_code=500, detail="Sorry not enough information")

@router.post("/company-query")
async def get_secure_company_info(
    request: Request,
    current_user: Profile = Depends(lambda token: get_current_user(token, Depends(get_session))),
    db: Session = Depends(get_session)
):
    """
    Get company information as an authenticated user
    """
    return company_query(current_user.id, request, db)






