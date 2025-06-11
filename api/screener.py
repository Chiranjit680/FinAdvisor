import logging
import asyncio
from datetime import datetime
from typing import Dict, List
import nsetools as nse
import yfinance as yf
from api.models import StockData
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Initialize NSE tools
nse_client = nse.Nse()

# def get_all_stock_codes():
#     """
#     Get all stock codes from NSE.
#     Returns a list or dictionary of stock codes.
#     """
#     try:
#         all_stock_codes = nse_client.get_stock_codes()
#         logger.info(f"Retrieved stock codes from NSE: {type(all_stock_codes)}")
#         logger.info(f"Sample data: {list(all_stock_codes)[:5] if hasattr(all_stock_codes, '__iter__') else str(all_stock_codes)[:100]}")
#         return all_stock_codes
#     except Exception as e:
#         logger.error(f"Error fetching stock codes from NSE: {str(e)}")
#         return []
def get_all_stock_codes():
    tickers = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "INFY",
    "HINDUNILVR",
    "KOTAKBANK",
    "SBIN",
    "LT",
    "ITC",
    "BAJFINANCE",
    "ASIANPAINT",
    "HDFC",
    "MARUTI",
    "AXISBANK",
    "SUNPHARMA",
    "WIPRO",
    "NESTLEIND",
    "BHARTIARTL",
    "ULTRACEMCO",
    "TITAN",
    "POWERGRID",
    "ONGC",
    "EICHERMOT",
    "DRREDDY",
    "DIVISLAB",
    "M&M",
    "TECHM",
    "COALINDIA",
    "JSWSTEEL"
]
    return tickers


def upload_stock_data(db: Session, batch_size: int = 50) -> Dict:
    """
    Upload/Update stock data from NSE to database with improved error handling.
    
    Args:
        db: Database session
        batch_size: Number of stocks to process in each batch
    
    Returns:
        Dictionary with operation results
    """
    logger.info("Starting stock data upload process...")
    
    try:
        all_stock_codes = get_all_stock_codes()
        
        if not all_stock_codes:
            logger.warning("No stock codes retrieved from NSE")
            return {
                "success": False,
                "message": "No stock codes available",
                "processed": 0,
                "errors": 0
            }
        
        total_stocks = len(all_stock_codes)
        processed_count = 0
        error_count = 0
        errors = []
        
        # Handle different data structures returned by NSE
        if isinstance(all_stock_codes, dict):
            # If it's a dictionary, use items()
            stock_items = list(all_stock_codes.items())
            logger.info(f"Processing {len(stock_items)} stocks from dictionary")
        elif isinstance(all_stock_codes, (list, tuple)):
            # If it's a list/tuple of stock codes, create pairs with None for company name
            stock_items = [(code, None) for code in all_stock_codes]
            logger.info(f"Processing {len(stock_items)} stocks from list/tuple")
        else:
            logger.error(f"Unexpected data type for stock codes: {type(all_stock_codes)}")
            return {
                "success": False,
                "message": f"Unexpected data type: {type(all_stock_codes)}",
                "processed": 0,
                "errors": 1
            }
        
        # Process stocks in batches to avoid overwhelming the API
        for i in range(0, len(stock_items), batch_size):
            batch = stock_items[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(stock_items) + batch_size - 1)//batch_size}")
            
            for item in batch:
                try:
                    # Handle both dictionary items (symbol, company_name) and list items (just symbol)
                    if isinstance(item, tuple) and len(item) == 2:
                        symbol, company_name = item
                    else:
                        symbol = item
                        company_name = None
                    # Add .NS suffix for NSE stocks in yfinance
                    yf_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
                    
                    stock_data = yf.Ticker(yf_symbol)
                    info = stock_data.info
                    
                    # Skip if no valid data is available
                    if not info or len(info) < 5:
                        logger.warning(f"No valid data for {symbol}")
                        continue
                    
                    # Extract stock information with safe defaults
                    # Since we don't have company_name from the list, use stock info
                    stock_name = info.get('shortName') or info.get('longName') or symbol or 'Unknown'
                    stock_ticker = info.get('symbol') or symbol
                    sector = info.get('sector') or 'Unknown'
                    stock_price = info.get('currentPrice') or info.get('regularMarketPrice', 0.0)
                    pe_ratio = info.get('trailingPE')
                    pb_ratio = info.get('priceToBook')
                    dividend_yield = info.get('dividendYield')
                    eps = info.get('forwardEps') or info.get('trailingEps')
                    book_value = info.get('bookValue')
                    market_cap = info.get('marketCap')
                    volume = info.get('volume') or info.get('regularMarketVolume')
                    
                    # Check if stock exists in database (using symbol instead of name)
                    existing_stock = db.exec(
    select(StockData).where(StockData.stock_ticker == stock_ticker)
).first()

                    
                    if existing_stock:
                        # Update existing stock data
                        existing_stock.stock_name = stock_name
                        existing_stock.stock_ticker = stock_ticker
                        existing_stock.sector = sector
                        existing_stock.current_price = stock_price
                        existing_stock.pe_ratio = pe_ratio
                        existing_stock.pb_ratio = pb_ratio
                        existing_stock.dividend_yield = dividend_yield
                        existing_stock.eps = eps
                        existing_stock.book_value = book_value
                        existing_stock.market_cap = market_cap
                        existing_stock.volume = volume
                        existing_stock.last_updated = datetime.utcnow()
                    else:
                        # Create new stock data
                        new_stock = StockData(
                            
                            stock_name=stock_name,
                            stock_ticker=stock_ticker,
                            sector=sector,
                            current_price=stock_price,
                            pe_ratio=pe_ratio,
                            pb_ratio=pb_ratio,
                            dividend_yield=dividend_yield,
                            eps=eps,
                            book_value=book_value,
                            market_cap=market_cap,
                            volume=volume,
                            last_updated=datetime.utcnow()
                        )
                        db.add(new_stock)
                    
                    processed_count += 1
                    logger.info(f"Processed {processed_count}/{total_stocks} stocks")
                    # Log progress every 100 stocks
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count}/{total_stocks} stocks")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Error processing {symbol}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
                    # Continue processing other stocks
                    continue
            
            # Commit batch to database
            try:
                db.commit()
                logger.info(f"Committed batch {i//batch_size + 1}")
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Error committing batch: {str(e)}")
                raise
        
        # Final commit
        db.commit()
        
        result = {
            "success": True,
            "message": f"Stock data upload completed successfully",
            "total_stocks": total_stocks,
            "processed": processed_count,
            "errors": error_count,
            "success_rate": f"{(processed_count/total_stocks)*100:.2f}%" if total_stocks > 0 else "0%"
        }
        
        if errors and len(errors) <= 10:  # Only include first 10 errors
            result["sample_errors"] = errors[:10]
        
        logger.info(f"Upload completed: {processed_count} processed, {error_count} errors")
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Critical error in upload_stock_data: {str(e)}")
        return {
            "success": False,
            "message": f"Critical error: {str(e)}",
            "processed": processed_count,
            "errors": error_count + 1
        }
