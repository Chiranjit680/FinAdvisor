
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Profile,Chat, Portfolio
from google import genai
import uuid
app = FastAPI()
from dotenv import load_dotenv
import os
from .middlewares import RateLimitMiddleware
load_dotenv()
app.add_middleware(RateLimitMiddleware, )
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
        
        # Optional: Save this conversation to database
        new_chat = Chat(
            user_id=user_id,
            human_message=prompt,
            ai_message=response.text
        )
        db.add(new_chat)
        db.commit()
        
        return {"response": response.text}
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e)+ " An error occurred while communicating with the Gemini API.")