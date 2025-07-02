from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from fastapi import HTTPException
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the system path if running directly
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from finagent
from FinAdvisor.agent.finagent import get_company_news, extract_company_ticker

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

def get_sentiment(prompt: str):
    """
    Get sentiment analysis for a specific company based on user prompt.
    """
    ticker = extract_company_ticker(prompt)
    company_news = get_company_news(prompt)
    if not company_news:
        logging.warning(f"No news found for ticker: {ticker}")
        company_news = "No news articles found for the specified company."
    sentiments = []
    for article in company_news:
        sentiment = analyze_sentiment(article['title'])
        sentiments.append(sentiment)
    return sentiments

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the sentiment analysis function
    prompt = "What is the latest news about Reliance Industries?"
    sentiments = get_sentiment(prompt)
    for sentiment in sentiments:
        print(f"Sentiment: {sentiment}")
