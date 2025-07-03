import sys
from pathlib import Path
import logging
import uuid
from typing import Any, Dict, List, Optional
import finnhub
from datetime import datetime, timedelta

# Langchain imports with correct paths
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
import langchain_core.output_parsers as output_parsers
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent  # Fixed import
from langchain.tools import tool
from FinAdvisor.api import models, database
import os
# Other imports
from dotenv import load_dotenv
from google import genai
from fastapi import HTTPException
import yfinance as yf
from sqlalchemy import select, desc

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Move these imports inside functions where they're needed
# from FinAdvisor.api import models, database

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Environment variables
google_api_key = os.getenv("GOOGLE_API_KEY")


# Initialize clients
try:
    client = genai.Client(api_key=google_api_key)
    logging.info("Gemini client initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Gemini client: {e}")
    client = None

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.2,
    api_key=google_api_key
)


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
        logging.warning("Gemini client not available, using fallback method")
        return _fallback_ticker_extraction(prompt)

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
        logging.error(f"Error extracting company name with Gemini: {e}")
        return _fallback_ticker_extraction(prompt)

def _fallback_ticker_extraction(prompt: str) -> str:
    """Fallback method for ticker extraction when Gemini is not available."""
    prompt_lower = prompt.lower()
    
    # Check for exact company name matches
    for company, ticker in company_ticker_map.items():
        if company.lower() in prompt_lower:
            return f"{ticker}.NS"
    
    # Check for ticker matches
    for ticker in company_ticker_map.values():
        if ticker.lower() in prompt_lower:
            return f"{ticker}.NS"
    
    # Default fallback
    logging.warning("No company found in prompt, defaulting to RELIANCE")
    return "RELIANCE.NS"

@tool
def query_stock_data(prompt: str) -> str:
    """
    Query stock data based on user prompt.
    Extracts company name and returns stock information.
    """
    # Import here to avoid circular imports
    
    
    try:
        ticker = extract_company_ticker(prompt)
        logging.info(f"Querying stock data for ticker: {ticker}")
        
        # Try to get data from database first
        db = database.get_db()
        if db:
            try:
                data = db.execute(
                    select(models.StockData).where(models.StockData.stock_ticker == ticker)
                ).fetchall()
                
                if data:
                    return f"Stock data from database: {data[0]}"
            except Exception as e:
                logging.error(f"Database query failed: {e}")
        
        # Fallback to Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d")
            
            if history.empty:
                return f"No stock data found for ticker '{ticker}'"
            
            info = stock.info
            current_price = history['Close'].iloc[-1]
            
            stock_info = {
                "ticker": ticker,
                "current_price": f"₹{current_price:.2f}",
                "sector": info.get('sector', 'Unknown'),
                "pe_ratio": info.get('forwardPE', 'N/A'),
                "pb_ratio": info.get('priceToBook', 'N/A'),
                "dividend_yield": info.get('dividendYield', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "volume": info.get('volume', 'N/A'),
                "last_updated": datetime.now().isoformat()
            }
            
            result = f"""
Stock Information for {ticker}:
- Current Price: {stock_info['current_price']}
- Sector: {stock_info['sector']}
- P/E Ratio: {stock_info['pe_ratio']}
- P/B Ratio: {stock_info['pb_ratio']}
- Dividend Yield: {stock_info['dividend_yield']}
- Market Cap: {stock_info['market_cap']}
- Volume: {stock_info['volume']}
- Last Updated: {stock_info['last_updated']}
            """
            
            return result.strip()
            
        except Exception as e:
            logging.error(f"Error fetching stock data from Yahoo Finance: {e}")
            return f"Failed to fetch stock data for {ticker}: {str(e)}"
            
    except Exception as e:
        logging.error(f"Error in query_stock_data: {e}")
        return f"Failed to process stock data query: {str(e)}"

@tool 
def get_company_news(prompt: str) -> str:
    """
    Fetch news articles and sentiment analysis for a specific company.
    """
    try:
        logging.info(f"Getting news and sentiment for prompt: {prompt}")
        news_sentiment = get_sentiment(prompt)
        
        if not news_sentiment:
            return "No news articles found for the specified company."
        
        if isinstance(news_sentiment, list) and len(news_sentiment) > 0:
            if news_sentiment[0].get('error'):
                return f"Error: {news_sentiment[0]['error']}"
        
        # Format the results for better readability
        result = "News Sentiment Analysis:\n\n"
        
        positive_count = 0
        negative_count = 0
        
        for i, item in enumerate(news_sentiment[:5], 1):  # Limit to top 5 articles
            if 'sentiment' in item:
                sentiment = item['sentiment']
                title = item.get('title', 'No title')[:100] + "..."
                
                result += f"{i}. {title}\n"
                result += f"   Sentiment: {sentiment['label']} (confidence: {sentiment['score']})\n\n"
                
                if sentiment['label'] == 'POSITIVE':
                    positive_count += 1
                else:
                    negative_count += 1
        
        result += f"Summary: {positive_count} positive, {negative_count} negative articles analyzed."
        
        return result
        
    except Exception as e:
        logging.error(f"Error in get_company_news: {e}")
        return f"Failed to fetch company news: {str(e)}"

@tool
def get_company_list() -> str:
    """Return list of available companies."""
    companies = list(company_ticker_map.keys())
    return f"Available companies for analysis:\n" + "\n".join([f"- {company}" for company in companies])

@tool
def get_ticker_by_company(company_name: str) -> str:
    """Get ticker symbol by exact company name match."""
    ticker = company_ticker_map.get(company_name)
    if ticker:
        return f"Ticker for {company_name}: {ticker}.NS"
    else:
        return f"Company '{company_name}' not found in our database."

@tool
def is_valid_ticker(ticker: str) -> str:
    """Check if ticker is valid."""
    # Remove .NS suffix for checking
    base_ticker = ticker.replace('.NS', '')
    is_valid = base_ticker in company_ticker_map.values()
    return f"Ticker '{ticker}' is {'valid' if is_valid else 'invalid'}."

# Define tools list
tools = [
    query_stock_data,
    get_company_news,
    get_company_list,
    get_ticker_by_company,
    is_valid_ticker
]

# Create prompt template
prompt_template = PromptTemplate(
    input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
    template="""You are FinGuru, an intelligent financial assistant that helps users manage their investments through natural conversation.

Your capabilities include:
- Fetching the latest news articles for a specific company and analyzing sentiment
- Providing comprehensive stock market data for Indian companies
- Answering general questions about companies and stocks
- Helping with investment decisions based on data analysis

You have access to these tools:
{tools}

Tool names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
)

# Create agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt_template
)

# Create agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    
    handle_parsing_errors=True,
    max_iterations=10
)

def financial_advice(user_id: uuid.UUID, query: str, db=None) -> Dict[str, Any]:
    """
    Generate financial advice based on user profile and query.
    """
    # Import here to avoid circular imports
    from FinAdvisor.api import models, database
    
    try:
        if not db:
            db = database.get_db()

        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if len(query) > 1000:
            raise HTTPException(status_code=400, detail="Query is too long. Please limit to 1000 characters.")

        # Get user history
        try:
            history = db.execute(
                select(models.Chat)
                .where(models.Chat.user_id == user_id)
                .order_by(desc(models.Chat.timestamp))
                .limit(5)
            ).fetchall()
            
            history_str = "\n".join([
                f"User: {chat.human_message} AI: {chat.ai_message}" 
                for chat in history
            ]) if history else "No previous conversation history."
            
        except Exception as e:
            logging.error(f"Error fetching chat history: {e}")
            history_str = "Unable to fetch conversation history."
        
        # Get user profile
        try:
            user_info = db.execute(
                select(models.Profile).where(models.Profile.id == user_id)
            ).first()
            
            portfolio = db.execute(
                select(models.Portfolio).where(models.Portfolio.user_id == user_id)
            ).first()
            
        except Exception as e:
            logging.error(f"Error fetching user data: {e}")
            user_info = None
            portfolio = None
        
        if not user_info:
            logging.warning(f"User {user_id} not found in database")
            user_context = "New user - no profile information available."
        else:
            user_context = f"User information: {user_info}"
            if portfolio:
                user_context += f"\nPortfolio information: {portfolio}"
        
        # Construct enhanced query with context
        enhanced_query = f"""
Context: {history_str}

{user_context}

This is a financial advisory session. Please provide comprehensive analysis and advice based on the user's question and available data.

User Question: {query}
        """
        
        # Execute agent
        response = agent_executor.invoke({"input": enhanced_query})
        
        if not response or 'output' not in response:
            raise HTTPException(status_code=500, detail="Failed to get a response from the financial advisor.")
        
        return {
            "response": response['output'],
            "user_id": str(user_id),
            "query": query
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error generating financial advice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate financial advice: {str(e)}")

# Test function
def test_financial_advice():
    """Test function for the financial advice system."""
    test_queries = [
        "What is the current price of Reliance Industries?",
        "Show me news sentiment for TCS",
        "Which companies are available for analysis?"
    ]
    
    test_user_id = uuid.uuid4()
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print('='*60)
        
        try:
            result = financial_advice(test_user_id, query)
            print(f"Response: {result['response']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_financial_advice()