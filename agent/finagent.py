import select
import uuid
from typing import Any, Dict, List, Optional
import finnhub
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
import langchain_core.output_parsers as output_parsers
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent
from langchain.tools import tool
from dotenv import load_dotenv
from google import genai
from fastapi import HTTPException
import logging
from FinAdvisor.api import models, database
import yfinance as yf
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from sqlalchemy import select
# from sentiment import analyze_sentiment
load_dotenv()
import os
google_api_key=os.getenv("GOOGLE_API_KEY")
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    logging.error(f"Failed to initialize Gemini client: {e}")
    client = None
llm= ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    api_key=google_api_key
)
finnhub_api_key = os.getenv("FINHUB")
finnhub_client = finnhub.Client(api_key=finnhub_api_key)
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
    Returns the NSE-compatible stock ticker symbol (e.g. RELIANCE.NS).
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
        logging.info(f"Gemini extracted name: {extracted_name}")

        ticker = company_ticker_map.get(extracted_name)
        if ticker:
            return f"{ticker}.NS"  # append .NS for Indian stocks

        # Fuzzy fallback: partial match
        for company_name in company_ticker_map.keys():
            if company_name.lower() in extracted_name.lower() or extracted_name.lower() in company_name.lower():
                return f"{company_ticker_map[company_name]}.NS"
        
        raise HTTPException(
            status_code=404, 
            detail=f"Company '{extracted_name}' not found in our database"
        )

    except Exception as e:
        logging.error(f"Error extracting company name: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract company name")




@tool
def query_stock_data(prompt: str) -> str:
    """
    Query stock data based on user prompt.
    Extracts company name, generates SQL query, and returns results.
    """
    
    db= database.get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database connection not initialized")

    try:
        
        ticker = extract_company_ticker(prompt)

        data = db.execute(select(models.StockData).where(models.StockData.stock_ticker == ticker)).fetchall()
        if not data:
            try:
                stock = yf.Ticker(ticker)
                history = stock.history(period="1d")
                if history.empty:
                    raise HTTPException(status_code=404, detail=f"No stock data found for ticker '{ticker}'")
                
                # Convert to a list of dictionaries for consistency
                sector = stock.info.get('sector', 'Unknown')
                current_price = history['Close'].iloc[-1]
                pe_ratio = stock.info.get('forwardPE', None)
                pb_ratio = stock.info.get('priceToBook', None)
                dividend_yield = stock.info.get('dividendYield', None)
                eps = stock.info.get('trailingEps', None)
                book_value = stock.info.get('bookValue', None)
                market_cap = stock.info.get('marketCap', None)
                volume = stock.info.get('volume', None)

                data = {
                    "stock_ticker": ticker,
                    "sector": sector,
                    "current_price": current_price,
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                    "dividend_yield": dividend_yield,
                    "eps": eps,
                    "book_value": book_value,
                    "market_cap": market_cap,
                    "volume": volume,
                    "last_updated": history.index[-1].isoformat()
                }
            except Exception as e:
                logging.error(f"Error fetching stock data from Yahoo Finance: {e}")
                raise HTTPException(status_code=500, detail="Failed to fetch stock data")

        return data
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error in query_stock_data: {e}")
        raise HTTPException(status_code=500, detail="Failed to process stock data query")
# Additional utility functions
@tool 
def get_company_news(prompt: str):
    """
    Fetch news articles related to a specific company.
    """
    ticker=extract_company_ticker(prompt)
    today=datetime.now().date()
    past=today - timedelta(days=30)
    company_news = finnhub_client.company_news(ticker, _from=past, to=today)
    
    return company_news
# @tool 
# def get_sentiment(prompt: str):
#     """
#     Get sentiment analysis for a specific company based on user prompt.
#     """
#     ticker=extract_company_ticker(prompt)
#     company_news = get_company_news(prompt)
#     sentiments = []
#     for article in company_news:
#         sentiment = analyze_sentiment(article['title'])
#         sentiments.append(sentiment)
#     return sentiments

@tool
def get_company_list() -> list:
    """Return list of available companies."""
    return list(company_ticker_map.keys())
@tool
def get_ticker_by_company(company_name: str) -> str:
    """Get ticker symbol by exact company name match."""
    return company_ticker_map.get(company_name)
@tool
def is_valid_ticker(ticker: str) -> bool:
    """Check if ticker is valid."""
    return ticker in company_ticker_map.values()
tools=[
    get_company_list,
    get_ticker_by_company,
    is_valid_ticker
]
# agent=create_react_agent(
#     llm=llm,
#     tools=tools,
#     prompt=prompt
# )

# Database schema context
# schema_context = """Table: stock_data
# Columns:
# - stock_id (UUID, primary key)
# - stock_name (TEXT)
# - stock_ticker (TEXT, unique)
# - sector (TEXT, optional)
# - current_price (FLOAT)
# - pe_ratio (FLOAT, optional)
# - pb_ratio (FLOAT, optional)
# - dividend_yield (FLOAT, optional)
# - eps (FLOAT, optional)
# - book_value (FLOAT, optional)
# - market_cap (FLOAT, optional)
# - volume (INTEGER, optional)
# - last_updated (TIMESTAMP with timezone)"""

# def generate_sql_query(prompt: str, ticker: str) -> str:
#     """Generate SQL query based on user prompt and ticker symbol."""
#     if not client:
#         raise HTTPException(status_code=500, detail="Gemini client not initialized")
    
#     llm_prompt = f"""
# User prompt: "{prompt}"
# Ticker: {ticker}

# Use the following table schema to write a valid SQL query.
# {schema_context}

# Important guidelines:
# - Only return the SQL query, no explanations or markdown formatting
# - Use the ticker symbol to filter results: WHERE stock_ticker = '{ticker}'
# - Ensure proper SQL syntax
# - Handle NULL values appropriately

# SQL Query:
# """
    
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash",
#             contents=llm_prompt
#         )
        
#         # Clean the response
#         sql_query = response.text.strip()
#         sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
#         return sql_query
        
#     except Exception as e:
#         logging.error(f"Error generating SQL query: {e}")
#         raise HTTPException(status_code=500, detail="Failed to generate SQL query")
