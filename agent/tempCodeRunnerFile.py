from datetime import datetime, timedelta
import finnhub
import sys
from pathlib import Path
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
import os
from dotenv import load_dotenv
load_dotenv()
finnhub_api_key = os.getenv("FINHUB")
finnhub_client = finnhub.Client(api_key=finnhub_api_key)

# Now import from finagent
from FinAdvisor.agent.finagent import  extract_company_ticker
def get_company_news(prompt: str):
    """
    Fetch news articles related to a specific company.
    """
    ticker=extract_company_ticker(prompt)
    today=datetime.now().date()
    past=today - timedelta(days=30)
    company_news = finnhub_client.company_news(ticker, _from=past, to=today)
    
    print(company_news)
    return company_news
if __name__ == "__main__":
    # Example usage
    prompt = "What is the latest news about Reliance Industries?"
    news = get_company_news(prompt)
    print(news)