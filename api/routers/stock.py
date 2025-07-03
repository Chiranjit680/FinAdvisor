import yfinance as yf
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..models import StockData
from ..database import get_session
from api import screener
from FinAdvisor.agent.sentiment import print_sentiment_summary, get_sentiment

router = APIRouter(
    prefix='/stock',
    tags=['Stock']
)

# Configure logging (add this if you don't have it elsewhere)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

@router.get('/fetch_stock_data/{ticker}')
async def fetch_stock_data(ticker: str, db: Session = Depends(get_session)):
    """
    Query stock data based on user prompt.
    Extracts company name and returns stock information.
    """
    logging.info(f"Fetching stock data for ticker: {ticker}")
    try:
        # Simple approach - just try to get the data directly
        stock = yf.Ticker(ticker)
        
        # Get basic info
        try:
            info = stock.info
            if not info or len(info) < 5:  # Basic check to see if we got meaningful data
                logging.warning(f"Got limited or no info for {ticker}: {info}")
                raise ValueError(f"Could not get sufficient data for {ticker}")
            
            # Get history data
            history = stock.history(period="1d")
            if history.empty:
                logging.warning(f"Got empty history for {ticker}")
                raise ValueError(f"Could not get price history for {ticker}")
            
            # Determine current price (try multiple sources)
            current_price = None
            if 'regularMarketPrice' in info and info['regularMarketPrice']:
                current_price = info['regularMarketPrice']
            elif 'currentPrice' in info and info['currentPrice']:
                current_price = info['currentPrice']
            elif not history.empty and 'Close' in history:
                current_price = history['Close'].iloc[-1]
                
            if current_price is None:
                logging.warning(f"Could not determine price for {ticker}")
                raise ValueError(f"Could not determine current price for {ticker}")
            
            # Create response with defensive gets to avoid KeyErrors
            stock_info = {
                "ticker": ticker,
                "current_price": current_price,
                "sector": info.get('sector', 'Unknown'),
                "pe_ratio": info.get('trailingPE', info.get('forwardPE', 'N/A')),
                "market_cap": info.get('marketCap', 'N/A'),
                "volume": info.get('volume', info.get('averageVolume', 'N/A')),
                "eps": info.get('trailingEps', 'N/A'),
                "open": info.get('open', info.get('regularMarketOpen', 'N/A')),
                "high": info.get('dayHigh', info.get('regularMarketDayHigh', 'N/A')),
                "low": info.get('dayLow', info.get('regularMarketDayLow', 'N/A')),
                "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
                "52_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
                "last_updated": datetime.now().isoformat()
            }
            
            logging.info(f"Successfully fetched data for {ticker}")
            return stock_info
            
        except Exception as e:
            logging.error(f"Error processing Yahoo Finance data: {str(e)}")
            
            # Try a fallback approach for Indian stocks
            fallback_ticker = ticker
            if ticker.endswith('.NS'):
                fallback_ticker = ticker[:-3]
            elif not ticker.endswith('.NS') and not ticker.endswith('.BO'):
                fallback_ticker = f"{ticker}.NS"
                
            logging.info(f"Trying fallback ticker: {fallback_ticker}")
            
            # Very simple fallback with minimal data
            try:
                stock = yf.Ticker(fallback_ticker)
                history = stock.history(period="1d")
                
                if history.empty:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No stock data found for ticker {ticker}"
                    )
                    
                # Just return basic price data
                return {
                    "ticker": ticker,
                    "current_price": history['Close'].iloc[-1] if not history.empty else 'N/A',
                    "open": history['Open'].iloc[-1] if not history.empty else 'N/A',
                    "high": history['High'].iloc[-1] if not history.empty else 'N/A',
                    "low": history['Low'].iloc[-1] if not history.empty else 'N/A',
                    "volume": history['Volume'].iloc[-1] if not history.empty else 'N/A',
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as fallback_err:
                logging.error(f"Fallback approach also failed: {str(fallback_err)}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Could not find stock data for {ticker} after multiple attempts"
                )
    except Exception as e:
        logging.error(f"Error in fetch_stock_data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock data: {str(e)}"
        )

@router.get('/display_news/{ticker}')
def display_stock_news(ticker: str):
    """
    Load stock data from NSE and update the database.
    """
    try:
        prompt= f" Fetch the latest news for the stock ticker {ticker} and analyse the sentiment of the news."
        sentiment = get_sentiment(prompt)

        if not sentiment:
            raise HTTPException(status_code=404, detail="No news found for this ticker")
        print_sentiment_summary(sentiment)
        print(sentiment )
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) + " An error occurred while fetching stock news.")
