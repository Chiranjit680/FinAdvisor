from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
import jwt  # This is PyJWT
from google import genai
import logging

load_dotenv()

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Gemini client with error handling
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    logging.error(f"Failed to initialize Gemini client: {e}")
    client = None

# Password utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# JWT token generation
def generate_jwt_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Generate a JWT token for a given user ID."""
    algorithm = "HS256"
    
    if expires_delta:
        expiration = datetime.utcnow() + expires_delta
    else:
        expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expiration
    }
    
    try:
        token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=algorithm)
        return token
    except Exception as e:
        logging.error(f"Failed to generate JWT token: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")

def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

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

def extract_company_ticker(prompt: str) -> str:
    """
    Extract and correct company name from prompt using Gemini.
    Returns the stock ticker symbol.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Gemini client not initialized")
    
    company_names = list(company_ticker_map.keys())
    company_names_str = ", ".join(company_names)
    
    context = (
        f"{prompt}\n\n"
        "Extract the company name from the above prompt.\n"
        "Correct any spelling or formatting mistakes.\n"
        "Only return the corrected, full company name.\n"
        "Example:\n"
        'User query: "show price of tata consultincy servises"\n'
        "Output: Tata Consultancy Services\n"
        f"Choose from the following company names:\n{company_names_str}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=context
        )
        
        extracted_name = response.text.strip()
        ticker = company_ticker_map.get(extracted_name)
        
        if ticker:
            return ticker
        else:
            # Fuzzy matching for similar company names
            for company_name in company_ticker_map.keys():
                if company_name.lower() in extracted_name.lower() or extracted_name.lower() in company_name.lower():
                    return company_ticker_map[company_name]
            
            raise HTTPException(
                status_code=404, 
                detail=f"Company '{extracted_name}' not found in our database"
            )
            
    except Exception as e:
        logging.error(f"Error extracting company name: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract company name")

# Database schema context
schema_context = """Table: stock_data
Columns:
- stock_id (UUID, primary key)
- stock_name (TEXT)
- stock_ticker (TEXT, unique)
- sector (TEXT, optional)
- current_price (FLOAT)
- pe_ratio (FLOAT, optional)
- pb_ratio (FLOAT, optional)
- dividend_yield (FLOAT, optional)
- eps (FLOAT, optional)
- book_value (FLOAT, optional)
- market_cap (FLOAT, optional)
- volume (INTEGER, optional)
- last_updated (TIMESTAMP with timezone)"""

def generate_sql_query(prompt: str, ticker: str) -> str:
    """Generate SQL query based on user prompt and ticker symbol."""
    if not client:
        raise HTTPException(status_code=500, detail="Gemini client not initialized")
    
    llm_prompt = f"""
User prompt: "{prompt}"
Ticker: {ticker}

Use the following table schema to write a valid SQL query.
{schema_context}

Important guidelines:
- Only return the SQL query, no explanations or markdown formatting
- Use the ticker symbol to filter results: WHERE stock_ticker = '{ticker}'
- Ensure proper SQL syntax
- Handle NULL values appropriately

SQL Query:
"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=llm_prompt
        )
        
        # Clean the response
        sql_query = response.text.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return sql_query
        
    except Exception as e:
        logging.error(f"Error generating SQL query: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")

# Additional utility functions
def get_company_list() -> list:
    """Return list of available companies."""
    return list(company_ticker_map.keys())

def get_ticker_by_company(company_name: str) -> str:
    """Get ticker symbol by exact company name match."""
    return company_ticker_map.get(company_name)

def is_valid_ticker(ticker: str) -> bool:
    """Check if ticker is valid."""
    return ticker in company_ticker_map.values()