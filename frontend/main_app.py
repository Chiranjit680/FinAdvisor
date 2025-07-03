import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configure the app
st.set_page_config(
    page_title="FinAdvisor",
    page_icon="💰",
    layout="wide"
)

# API endpoint
API_URL = "http://localhost:8000"

# Stock ticker mapping
STOCK_TICKERS = {
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

# Dropdown options
MARITAL_STATUS_OPTIONS = ["Single", "Married", "Divorced", "Widowed", "Separated"]
OCCUPATION_OPTIONS = ["Software Engineer", "Doctor", "Teacher", "Business Owner", "Consultant", "Manager", "Other"]
LOCATION_OPTIONS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Other"]

# Utility functions
def show_error(message):
    st.error(message)

def show_success(message):
    st.success(message)

def api_request(method, url, **kwargs):
    """Make API request with retry logic for rate limiting"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            if method.lower() == 'get':
                response = requests.get(url, **kwargs)
            elif method.lower() == 'post':
                response = requests.post(url, **kwargs)
            elif method.lower() == 'put':
                response = requests.put(url, **kwargs)
            else:
                show_error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    with st.spinner(f"Rate limit exceeded. Retrying in {retry_delay} seconds..."):
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    continue
            return response
            
        except Exception as e:
            show_error(f"API request error: {str(e)}")
            return None
    
    show_error("Maximum retry attempts reached")
    return None

# Authentication functions
def login(username, password):
    """Login user"""
    try:
        response = api_request(
            'post', 
            f"{API_URL}/user/token",
            data={"username": username, "password": password}
        )
        
        if not response:
            return False
            
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_token = data["access_token"]
            st.session_state.user_id = data["user_id"]
            st.session_state.username = username
            st.session_state.authenticated = True
            st.session_state.page = "portfolio"
            show_success("Login successful!")
            st.rerun()  
            return True
        else:
            error_msg = "Invalid username or password"
            try:
                error_msg = response.json().get("detail", error_msg)
            except:
                pass
            show_error(error_msg)
            return False
    except Exception as e:
        show_error(f"Login error: {str(e)}")
        return False

def register(username, password, email, name, age):
    """Register new user"""
    try:
        user_data = {
            "username": username,
            "password": password,
            "email": email,
            "name": name,
            "age": int(age)
        }
        
        response = api_request(
            'post',
            f"{API_URL}/user/create_profile",
            json=user_data
        )
        
        if not response:
            return False
            
        if response.status_code in (200, 201):
            show_success("Registration successful! Please login.")
            st.session_state.page = "login"
            return True
        else:
            error_msg = "Registration failed"
            try:
                error_msg = response.json().get("detail", error_msg)
            except:
                pass
            show_error(error_msg)
            return False
    except Exception as e:
        show_error(f"Registration error: {str(e)}")
        return False

def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    st.session_state.user_token = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.page = "login"
    show_success("You have been logged out.")

# Portfolio functions
def get_portfolio_data():
    """Get portfolio data"""
    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
    
    response = api_request(
        'get',
        f"{API_URL}/portfolio/secure/my_portfolio",
        headers=headers
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return {}  # Empty portfolio
    else:
        show_error(f"Failed to get portfolio: {response.status_code}")
        return None
def create_portfolio(portfolio_data):
    """Create a new portfolio"""
    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
    response = api_request(
        'post',
        f"{API_URL}/portfolio/secure/add_portfolio",
        headers=headers,
        json=portfolio_data
    )
    if not response:
        return None
    if response.status_code == 201:
        show_success("Portfolio created successfully!")
        return response.json()
    else:
        show_error(f"Failed to create portfolio: {response.status_code}")
        return None

def update_portfolio(portfolio_data):
    """Update portfolio data"""
    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
    
    response = api_request(
        'put',
        f"{API_URL}/portfolio/secure/update_portfolio",
        headers=headers,
        json=portfolio_data
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        show_success("Portfolio updated successfully!")
        return response.json()
    else:
        show_error(f"Failed to update portfolio: {response.status_code}")
        return None

# Stock functions
def get_stock_data(ticker):
    """Get stock data"""
    response = api_request(
        'get',
        f"{API_URL}/stock/fetch_stock_data/{ticker}"
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        return response.json()
    else:
        show_error(f"Failed to get stock data: {response.status_code}")
        return None

def get_stock_sentiment(ticker):
    """Get stock sentiment analysis"""
    response = api_request(
        'get',
        f"{API_URL}/stock/display_news/{ticker}"
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        return response.json()
    else:
        show_error(f"Failed to get sentiment data: {response.status_code}")
        return None

# Personal info functions
def get_personal_info():
    """Get personal info"""
    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
    
    response = api_request(
        'get',
        f"{API_URL}/user/me/personal_info",
        headers=headers
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        return response.json().get("personal_info")
    elif response.status_code == 404:
        return {}  # No personal info yet
    else:
        show_error(f"Failed to get personal info: {response.status_code}")
        return None

def update_personal_info(personal_data):
    """Update personal info"""
    headers = {"Authorization": f"Bearer {st.session_state.user_token}"}
    
    response = api_request(
        'post',
        f"{API_URL}/user/add_personal_details/",
        headers=headers,
        json=personal_data
    )
    
    if not response:
        return None
        
    if response.status_code == 200:
        show_success("Personal information updated successfully!")
        return response.json()
    else:
        show_error(f"Failed to update personal info: {response.status_code}")
        return None

def send_message(message, user_token):
    """Send a message to the chat API"""
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.post(
            f"{API_URL}/chat/secure-advice",
            json={"prompt": message},  # Changed "message" to "prompt"
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error sending message: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the server. Please make sure the backend is running.")
        return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Page functions
def show_login_page():
    st.title("Login to FinAdvisor")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/graph.png", width=100)
    with col2:
        st.markdown("## Welcome back!")
    
    # Form for login
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Form buttons must be inside the form
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Login")
        with col2:
            register_button = st.form_submit_button("Register Instead")
        
        if submit:
            if username and password:
                login(username, password)
                return
            else:
                show_error("Please enter both username and password")
                
    # Handle register button click outside the form
    if register_button:
        st.session_state.page = "register"
        st.rerun()

def show_register_page():
    st.title("Create an Account")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username")
            email = st.text_input("Email")
            name = st.text_input("Full Name")
        
        with col2:
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            age = st.number_input("Age", min_value=18, max_value=100, value=25)
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if not all([username, email, name, password, confirm_password]):
                show_error("Please fill all fields")
            elif password != confirm_password:
                show_error("Passwords don't match")
            else:
                register(username, password, email, name, age)

def show_portfolio_page():
    st.title("Portfolio Management")
    
    # Get portfolio data
    portfolio_data = get_portfolio_data()
    
    if portfolio_data is None:
        st.warning("Error loading portfolio data")
        return
    
    # Display portfolio or create new one
    if portfolio_data:
        # Create tabs
        tab1, tab2 = st.tabs(["Portfolio Overview", "Update Portfolio"])
        
        with tab1:
            # Calculate total value
            total = sum([
                portfolio_data.get("equity_amt", 0),
                portfolio_data.get("cash_amt", 0),
                portfolio_data.get("fd_amt", 0),
                portfolio_data.get("debt_amt", 0),
                portfolio_data.get("real_estate_amt", 0),
                portfolio_data.get("bonds_amt", 0),
                portfolio_data.get("crypto_amt", 0)
            ])
            
            st.header(f"Total Portfolio Value: ₹{total:,.2f}")
            
            # Create portfolio pie chart
            categories = ["Equity", "Cash", "Fixed Deposits", "Debt", "Real Estate", "Bonds", "Crypto"]
            values = [
                portfolio_data.get("equity_amt", 0),
                portfolio_data.get("cash_amt", 0),
                portfolio_data.get("fd_amt", 0),
                portfolio_data.get("debt_amt", 0),
                portfolio_data.get("real_estate_amt", 0),
                portfolio_data.get("bonds_amt", 0),
                portfolio_data.get("crypto_amt", 0)
            ]
            
            # Filter out zero values
            filtered_data = [(cat, val) for cat, val in zip(categories, values) if val > 0]
            if filtered_data:
                filtered_cats, filtered_vals = zip(*filtered_data)
                
                fig = px.pie(
                    values=filtered_vals,
                    names=filtered_cats,
                    title="Portfolio Allocation"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No portfolio data to display")
        
        with tab2:
            with st.form("update_portfolio"):
                st.subheader("Update Your Portfolio")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    equity = st.number_input("Equity Amount (₹)", 
                                          min_value=0.0, 
                                          value=float(portfolio_data.get("equity_amt", 0)))
                    
                    cash = st.number_input("Cash Amount (₹)", 
                                         min_value=0.0, 
                                         value=float(portfolio_data.get("cash_amt", 0)))
                    
                    fd = st.number_input("Fixed Deposit Amount (₹)", 
                                       min_value=0.0, 
                                       value=float(portfolio_data.get("fd_amt", 0)))
                    
                    debt = st.number_input("Debt Amount (₹)", 
                                         min_value=0.0, 
                                         value=float(portfolio_data.get("debt_amt", 0)))
                
                with col2:
                    real_estate = st.number_input("Real Estate Amount (₹)", 
                                                min_value=0.0, 
                                                value=float(portfolio_data.get("real_estate_amt", 0)))
                    
                    bonds = st.number_input("Bonds Amount (₹)", 
                                          min_value=0.0, 
                                          value=float(portfolio_data.get("bonds_amt", 0)))
                    
                    crypto = st.number_input("Cryptocurrency Amount (₹)", 
                                           min_value=0.0, 
                                           value=float(portfolio_data.get("crypto_amt", 0)))
                
                submitted = st.form_submit_button("Update Portfolio")
                
                if submitted:
                    updated_data = {
                        "equity_amt": equity,
                        "cash_amt": cash,
                        "fd_amt": fd,
                        "debt_amt": debt,
                        "real_estate_amt": real_estate,
                        "bonds_amt": bonds,
                        "crypto_amt": crypto
                    }
                    
                    if update_portfolio(updated_data):
                        st.rerun()
    else:
        st.info("You don't have a portfolio yet. Let's create one!")
        
        # Fix: Add try-except block properly
        try:
            with st.form("create_portfolio"):
                st.subheader("Create Your Portfolio")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    equity = st.number_input("Equity Amount (₹)", min_value=0.0, value=0.0)
                    cash = st.number_input("Cash Amount (₹)", min_value=0.0, value=0.0)
                    fd = st.number_input("Fixed Deposit Amount (₹)", min_value=0.0, value=0.0)
                    debt = st.number_input("Debt Amount (₹)", min_value=0.0, value=0.0)
                
                with col2:
                    real_estate = st.number_input("Real Estate Amount (₹)", min_value=0.0, value=0.0)
                    bonds = st.number_input("Bonds Amount (₹)", min_value=0.0, value=0.0)
                    crypto = st.number_input("Cryptocurrency Amount (₹)", min_value=0.0, value=0.0)
                
                submitted = st.form_submit_button("Create Portfolio")
                
                if submitted:
                    new_data = {
                        "equity_amt": equity,
                        "cash_amt": cash,
                        "fd_amt": fd,
                        "debt_amt": debt,
                        "real_estate_amt": real_estate,
                        "bonds_amt": bonds,
                        "crypto_amt": crypto
                    }

                    if create_portfolio(new_data):
                        st.rerun()
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def show_stock_page():
    st.title("Stock Analysis")
    
    # Stock selection
    company_name = st.selectbox("Select a company", options=list(STOCK_TICKERS.keys()))
    ticker = f"{STOCK_TICKERS[company_name]}.NS"


    st.header(f"{company_name} ({ticker})")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Stock Data", "Sentiment Analysis"])
    
    with tab1:
        with st.spinner("Loading stock data..."):
            stock_data = get_stock_data(ticker)
        
        if stock_data and len(stock_data) > 0:
            # Display stock data
            latest_data = stock_data[0] if isinstance(stock_data, list) else stock_data
            
            # Show key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Price", f"₹{latest_data.get('current_price', 0):,.2f}")
                st.metric("P/E Ratio", str(latest_data.get('pe_ratio', 'N/A')))
            
            with col2:
                st.metric("Market Cap", f"₹{latest_data.get('market_cap', 0):,.2f}")
                st.metric("Volume", f"{latest_data.get('volume', 0):,}")
            
            with col3:
                st.metric("EPS", f"₹{latest_data.get('eps', 0):,.2f}")
                st.metric("Dividend Yield", f"{latest_data.get('dividend_yield', 0):.2f}%")
            
            # Display full data table
            st.subheader("Complete Stock Data")
            st.dataframe(pd.DataFrame([latest_data]), use_container_width=True)
        else:
            st.error(f"No data available for {ticker}")
    
    with tab2:
        if st.button("Analyze Sentiment"):
            with st.spinner("Analyzing sentiment..."):
                sentiment = get_stock_sentiment(ticker)
            
            if sentiment:
                st.success("Sentiment analysis completed")
                count = {"Positive": 0, "Neutral": 0, "Negative": 0}
                
                for item in sentiment:
                    title = item.get("title", "No title")
                    sen = item.get("sentiment", "Neutral")
                    if isinstance(sen, dict) and "label" in sen:
                        sen = sen.get("label")  # Extract label if sentiment is a dictionary
                    st.subheader(title)
                    st.write(f"Sentiment: {sen}")
                    
                    if sen == "POSITIVE":
                        count["Positive"] += 1
                    elif sen == "NEGATIVE":
                        count["Negative"] += 1
                    else:
                        count["Neutral"] += 1

                # Create pie chart
                fig = px.pie(
                    values=list(count.values()),
                    names=list(count.keys()),
                    title="Sentiment Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Show individual news items
                for i, item in enumerate(sentiment):  # Changed 'sentiments' to 'sentiment'
                    with st.expander(f"News {i+1}"):
                        st.write(item.get("content", "No content"))
                        link = item.get("link", "")
                        if link:
                            st.markdown(f"[Read more]({link})")
                        
                        sentiment_value = item.get("sentiment", "Neutral")
                        if isinstance(sentiment_value, dict) and "label" in sentiment_value:
                            sentiment_value = sentiment_value.get("label")
                        
                        if sentiment_value == "POSITIVE":
                            st.success(f"Sentiment: {sentiment_value}")
                        elif sentiment_value == "NEGATIVE":
                            st.error(f"Sentiment: {sentiment_value}")
                        else:
                            st.info(f"Sentiment: {sentiment_value}")
            else:
                st.error("Failed to get sentiment analysis")

def show_personal_page():
    st.title("Personal Information")
    
    # Get personal info
    personal_data = get_personal_info()
    
    if personal_data is None:
        st.warning("Error loading personal information")
        return
    
    # Display form
    with st.form("update_personal_info"):
        st.subheader("Your Personal Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.selectbox(
                "Location",
                options=LOCATION_OPTIONS,
                index=LOCATION_OPTIONS.index(personal_data.get("location", "Other")) if personal_data.get("location") in LOCATION_OPTIONS else len(LOCATION_OPTIONS)-1
            )
            
            occupation = st.selectbox(
                "Occupation",
                options=OCCUPATION_OPTIONS,
                index=OCCUPATION_OPTIONS.index(personal_data.get("occupation", "Other")) if personal_data.get("occupation") in OCCUPATION_OPTIONS else len(OCCUPATION_OPTIONS)-1
            )
            
            if occupation == "Other":
                occupation = st.text_input("Specify Occupation", value=personal_data.get("occupation", "") if personal_data.get("occupation") not in OCCUPATION_OPTIONS else "")
            
            marital_status = st.selectbox(
                "Marital Status",
                options=MARITAL_STATUS_OPTIONS,
                index=MARITAL_STATUS_OPTIONS.index(personal_data.get("marital_status", "Single")) if personal_data.get("marital_status") in MARITAL_STATUS_OPTIONS else 0
            )
        
        with col2:
            dependants = st.number_input(
                "Number of Dependants",
                min_value=0,
                max_value=10,
                value=int(personal_data.get("dependants", 0))
            )
            
            income = st.number_input(
                "Monthly Income (₹)",
                min_value=0.0,
                value=float(personal_data.get("income", 0))
            )
        
        submitted = st.form_submit_button("Save Information")
        
        if submitted:
            updated_data = {
                "location": location,
                "occupation": occupation,
                "marital_status": marital_status,
                "dependants": dependants,
                "income": income
            }
            
            if update_personal_info(updated_data):
                st.rerun()
    
    # Display financial insights if data exists
    if personal_data and personal_data.get("income"):
        st.subheader("Financial Insights")
        
        # Simple financial analysis
        income = personal_data.get("income", 0)
        dependants = personal_data.get("dependants", 0)
        
        # Basic calculations
        monthly_expenses = income * 0.6  # Estimated expenses
        if dependants > 0:
            monthly_expenses += income * 0.1 * dependants  # Additional expenses per dependant
        
        savings = max(income - monthly_expenses, 0)
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Monthly Income", f"₹{income:,.2f}")
        
        with col2:
            st.metric("Estimated Expenses", f"₹{monthly_expenses:,.2f}")
        
        with col3:
            st.metric("Potential Savings", f"₹{savings:,.2f}", f"{savings_rate:.1f}%")
        
        # Financial recommendations
        st.subheader("Recommendations")
        
        if savings_rate < 20:
            st.warning("Your savings rate is below recommended levels. Consider reducing expenses.")
        else:
            st.success("You have a healthy savings rate. Consider investing your surplus.")

def show_chat_page():
    """Display the chat page"""
    st.title("💬 Financial Chat Advisor")
    st.markdown("### Ask me anything about finance, investments, and market analysis!")
    
    # Initialize chat messages if not already done
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="🙋‍♂️"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your financial question here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar="🙋‍♂️"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                if st.session_state.get('user_token'):
                    # Send to API
                    response = send_message(prompt, st.session_state.user_token)
                    if response and "response" in response:
                        ai_response = response["response"]
                    else:
                        ai_response = "I'm sorry, I couldn't process your request at the moment. Please try again."
                else:
                    # Mock response if no API connection
                    ai_response = f"I understand you're asking about: '{prompt}'. This is a mock response since the backend isn't connected. In a real scenario, I would provide detailed financial advice based on your query."
                
                st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Sidebar with chat options
    with st.sidebar:
        st.markdown("---")
        st.subheader("💬 Chat Options")
        
       
        # Sample questions
        st.markdown("---")
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "How should I diversify my portfolio?",
            "What's the difference between stocks and bonds?",
            "How much should I save for retirement?",
            "What are the best investment strategies for beginners?",
            "How do I analyze a stock's performance?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(f"❓ {question}", key=f"sample_{i}", use_container_width=True):
                # Add the sample question to chat
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()
        
        # Chat statistics
        if st.session_state.messages:
            st.markdown("---")
            st.subheader("📊 Chat Stats")
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            ai_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your Messages", user_messages)
            with col2:
                st.metric("AI Responses", ai_messages)

# Main function
def main():
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "page" not in st.session_state:
        st.session_state.page = "login"
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Sidebar
    with st.sidebar:
        st.title("FinAdvisor")
        st.markdown("---")
        
        if st.session_state.authenticated:
            st.success(f"Logged in as: {st.session_state.username}")
            st.markdown("---")
            
            # Navigation
            if st.button("💬 Chat Advisor", use_container_width=True, key="btn_chat"):
                st.session_state.page = "chat"
                st.rerun()
                
            if st.button("📊 Portfolio", use_container_width=True, key="btn_portfolio"):
                st.session_state.page = "portfolio"
                st.rerun()
            
            if st.button("📈 Stock Analysis", use_container_width=True, key="btn_stocks"):
                st.session_state.page = "stocks"
                st.rerun()
            
            if st.button("👤 Personal Info", use_container_width=True, key="btn_personal"):
                st.session_state.page = "personal"
                st.rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True, key="btn_logout"):
                logout()
                st.rerun()
        else:
            auth_option = st.radio("Select Option", ["Login", "Register"], key="auth_radio")
            
            if auth_option == "Login":
                st.session_state.page = "login"
            else:
                st.session_state.page = "register"
    
    # Page routing
    if not st.session_state.authenticated:
        if st.session_state.page == "login":
            show_login_page()
        elif st.session_state.page == "register":
            show_register_page()
    else:
        if st.session_state.page == "chat":
            show_chat_page()
        elif st.session_state.page == "portfolio":
            show_portfolio_page()
        elif st.session_state.page == "stocks":
            show_stock_page()
        elif st.session_state.page == "personal":
            show_personal_page()


















if __name__ == "__main__":
    main()