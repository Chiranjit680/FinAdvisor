from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
import jwt  # This is PyJWT
from google import genai
import logging
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    logging.error(f"Failed to initialize Gemini client: {e}")
    client = None
# Load environment variables
load_dotenv()
# Gemini chat function
def chat_with_gemini(prompt: str) -> str:
    """Chat with Gemini AI model."""
    if not client:
        raise HTTPException(status_code=500, detail="Gemini client not initialized")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail="AI service unavailable")

# Company ticker mapping
company_ticker_map = {
    "Reliance Industries": "RELIANCE",
    "Tata Consultancy Services": "TCS",
    "HDFC Bank": "HDFCBANK",
    "ICICI Bank": "ICICIBANK",
    "Infosys": "INFY",
    "Hindustan Unilever": "HINDUNILVR",
    "Kotak Mahindra Bank": "KOTAKBANK",
    "State Bank of India": "SBIN",
    "Larsen & Toubro": "LT",
    "ITC": "ITC",
    "Bajaj Finance": "BAJFINANCE",
    "Asian Paints": "ASIANPAINT",
    "Housing Development Finance Corporation": "HDFC",
    "Maruti Suzuki": "MARUTI",
    "Axis Bank": "AXISBANK",
    "Sun Pharmaceutical": "SUNPHARMA",
    "Wipro": "WIPRO",
    "Nestle India": "NESTLEIND",
    "Bharti Airtel": "BHARTIARTL",
    "UltraTech Cement": "ULTRACEMCO",
    "Titan Company": "TITAN",
    "Power Grid Corporation": "POWERGRID",
    "Oil and Natural Gas Corporation": "ONGC",
    "Eicher Motors": "EICHERMOT",
    "Dr. Reddy's Laboratories": "DRREDDY",
    "Divi's Laboratories": "DIVISLAB",
    "Mahindra & Mahindra": "M&M",
    "Tech Mahindra": "TECHM",
    "Coal India": "COALINDIA",
    "JSW Steel": "JSWSTEEL"
}
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)   