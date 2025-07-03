from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from fastapi import HTTPException
import requests
from bs4 import BeautifulSoup
import logging
import os
import sys
import re
from pathlib import Path

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

# Reverse mapping for ticker to company name
ticker_company_map = {v: k for k, v in company_ticker_map.items()}

# Use a pre-trained sentiment model from Hugging Face
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

try:
    # Use AutoTokenizer and AutoModel to automatically determine the correct model class
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    logging.info(f"Successfully loaded sentiment model: {MODEL_NAME}")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    raise RuntimeError(f"Failed to load sentiment model: {e}")

def analyze_sentiment(text: str):
    """
    Analyze sentiment of the given text using a pre-trained model.
    Returns sentiment label and score.
    """
    try:
        result = sentiment_pipeline(text)[0]
        return {
            "label": result['label'],
            "score": round(result['score'], 3)
        }
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")

def extract_keyword_context(text, keyword, context_size=50):
    """Extract context around keywords in text."""
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    matches = pattern.finditer(text)
    results = []
    for match in matches:
        start_index = max(match.start() - context_size, 0)
        end_index = min(match.end() + context_size, len(text))
        context_snippet = text[start_index:end_index]
        results.append(context_snippet)
    return results

def extract_company_ticker(prompt: str):
    """
    Extract company ticker from prompt.
    This is a simplified version - you may need to implement more sophisticated NLP.
    """
    prompt_lower = prompt.lower()
    
    # Check for exact company name matches
    for company, ticker in company_ticker_map.items():
        if company.lower() in prompt_lower:
            return ticker
    
    # Check for ticker matches
    for ticker in company_ticker_map.values():
        if ticker.lower() in prompt_lower:
            return ticker
    
    # Default fallback - you might want to handle this differently
    return "RELIANCE"

def scraping_google_news(ticker: str):
    """
    Scrape Google News RSS for company-related news.
    Returns a list of news articles with title and description.
    """
    try:
        # Get company name for better search results
        company_name = ticker_company_map.get(ticker, ticker)
        
        # Use both ticker and company name in search
        search_query = f"{ticker}+{company_name.replace(' ', '+')}+stock"
        url = f"https://news.google.com/rss/search?q={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            articles = []
            keywords = [ticker, company_name]
            
            for item in items[:10]:  # Limit to first 10 articles
                title = item.title.get_text() if item.title else ""
                description = item.description.get_text() if item.description else ""
                link = item.link.get_text() if item.link else ""
                pub_date = item.pubDate.get_text() if item.pubDate else ""
                
                # Check if article is relevant to our company
                full_text = (title + " " + description).lower()
                is_relevant = any(keyword.lower() in full_text for keyword in keywords)
                
                if is_relevant and title:  # Only include if relevant and has title
                    articles.append({
                        'title': title,
                        'description': description,
                        'link': link,
                        'pub_date': pub_date
                    })
            
            return articles
        else:
            logging.error(f"Failed to fetch news. Status code: {response.status_code}")
            return []
            
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return []
    except Exception as e:
        logging.error(f"Error scraping news: {e}")
        return []

def get_sentiment(prompt: str):
    """
    Get sentiment analysis for a specific company based on user prompt.
    Returns a list of sentiment analysis results for news articles.
    """
    try:
        # Extract ticker from prompt
        ticker = extract_company_ticker(prompt)
        logging.info(f"Extracted ticker: {ticker}")
        
        # Get news articles
        company_news = scraping_google_news(ticker)
        
        if not company_news:
            logging.warning(f"No news found for ticker: {ticker}")
            return [{
                "error": "No news articles found for the specified company.",
                "ticker": ticker
            }]
        
        # Analyze sentiment for each article
        sentiments = []
        for article in company_news:
            try:
                # Analyze sentiment of title (and description if available)
                text_to_analyze = article['title']
                if article.get('description'):
                    text_to_analyze += " " + article['description']
                
                sentiment = analyze_sentiment(text_to_analyze)
                
                sentiments.append({
                    'title': article['title'],
                    'sentiment': sentiment,
                    'link': article.get('link', ''),
                    'pub_date': article.get('pub_date', '')
                })
                
            except Exception as e:
                logging.error(f"Error analyzing sentiment for article: {e}")
                continue
        
        return sentiments
        
    except Exception as e:
        logging.error(f"Error in get_sentiment: {e}")
        return [{"error": f"Failed to analyze sentiment: {str(e)}"}]

def print_sentiment_summary(sentiments):
    """Print a formatted summary of sentiment analysis results."""
    if not sentiments:
        print("No sentiment data available.")
        return
    
    if sentiments[0].get('error'):
        print(f"Error: {sentiments[0]['error']}")
        return
    
    print(f"\n=== Sentiment Analysis Summary ===")
    print(f"Total articles analyzed: {len(sentiments)}")
    
    # Count sentiment distribution
    positive_count = sum(1 for s in sentiments if s['sentiment']['label'] == 'POSITIVE')
    negative_count = sum(1 for s in sentiments if s['sentiment']['label'] == 'NEGATIVE')
    
    print(f"Positive sentiment: {positive_count}")
    print(f"Negative sentiment: {negative_count}")
    
    # Calculate average confidence
    avg_confidence = sum(s['sentiment']['score'] for s in sentiments) / len(sentiments)
    print(f"Average confidence: {avg_confidence:.3f}")
    news_articles = [f"{sentiment['title'][:100]}... (Sentiment: {sentiment['sentiment']['label']}, Confidence: {sentiment['sentiment']['score']})" for sentiment in sentiments]
    print(f"\n=== Individual Articles ===")
    for i, sentiment in enumerate(sentiments, 1):
        print(f"\n{i}. {sentiment['title'][:100]}...")
        print(f"   Sentiment: {sentiment['sentiment']['label']} (confidence: {sentiment['sentiment']['score']})")
        if sentiment.get('pub_date'):
            print(f"   Published: {sentiment['pub_date']}")
    return news_articles
    

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the sentiment analysis function
    test_prompts = [
        "What is the latest news about Reliance Industries?",
        "Show me TCS stock sentiment",
        "HDFC Bank news analysis"
    ]
    
    for prompt in test_prompts:
        print(f"\n" + "="*60)
        print(f"Testing prompt: {prompt}")
        print("="*60)
        
        sentiments = get_sentiment(prompt)
        print_sentiment_summary(sentiments)