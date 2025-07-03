# FinAdvisor
# 📊 FinAdvisor

> Your AI-powered personal finance and investment advisor, powered by LangChain ReAct Agents, FastAPI, and contextual intelligence.

---

## 🌟 Overview

**FinAdvisor** is an intelligent backend platform designed to assist users in making informed investment decisions through natural language queries and personalized insights. It combines **context-aware AI agents**, **live stock market data**, and **portfolio tracking** to simulate a real financial advisor experience — tailored just for you.

The project is modular and scalable, serving as a backend for finance bots, apps, or dashboards.

---

## 🚀 Features

- 🤖 **ReAct Agent for Finance**:  
  Uses LangChain’s ReAct (Reasoning + Acting) paradigm to fetch data, reason about user goals, and respond intelligently.

- 🧠 **Context-Aware Advisory**:  
  Understands your portfolio, preferences, and risk appetite to give contextual recommendations.

- 📦 **Stock Data from DB or yFinance**:  
  Efficient caching and querying via a SQLModel-powered database; with live fallback using Yahoo Finance API (`yfinance`).

- 📰 **Live Stock News + Sentiment Analysis**:  
  Scrapes Google News for stock tickers using `BeautifulSoup`, performs NLP sentiment analysis, and summarizes it.

- 📈 **Portfolio Tracking & Personalization**:  
  Users can add stocks to their portfolio, and the agent responds accordingly with suggestions tailored to their current holdings.

- ⚙️ **RESTful APIs with FastAPI**:  
  Exposes endpoints to fetch, update, and personalize financial data — ready to integrate with any frontend or bot.

---

## 🛠️ Tech Stack

| Component        | Technology                    |
|------------------|------------------------------ |
| Backend Framework | FastAPI                      |
| Agent Framework   | LangChain ReAct Agents       |
| Database          | SQLModel + SQLite            |
| Financial Data    | yFinance API                 |
| Web Scraping      | BeautifulSoup + requests     |
| Sentiment Analysis| Custom NLP Agent / OpenAI    |
| Front end         | Streamlit                    |

---
