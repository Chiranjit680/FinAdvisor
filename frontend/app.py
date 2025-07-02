import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# Constants
API_URL = "http://localhost:8000"

# Set page configuration
st.set_page_config(
    page_title="FinAdvisor - Your Personal Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "token" not in st.session_state:
    st.session_state.token = None
if "user_data" not in st.session_state:
    st.session_state.user_data = None

def login(username, password):
    """Authenticate user and store token"""
    try:
        response = requests.post(
            f"{API_URL}/user/token",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            # Get user profile after login
            get_user_profile()
            return True
        else:
            st.error(f"Login failed: {response.text}")
            return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def get_user_profile():
    """Get user profile data"""
    if not st.session_state.token:
        return None
        
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_URL}/user/me", headers=headers)
        
        if response.status_code == 200:
            st.session_state.user_data = response.json()
            return st.session_state.user_data
        else:
            st.error(f"Failed to get profile: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error getting profile: {str(e)}")
        return None

def get_portfolio():
    """Get user portfolio data"""
    if not st.session_state.token:
        return None
        
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_URL}/portfolio/secure/my_portfolio", headers=headers)
        
        if response.status_code == 200:
            return response.json()["portfolio"]
        else:
            return None
    except Exception as e:
        st.error(f"Error getting portfolio: {str(e)}")
        return None

def get_financial_advice(prompt):
    """Get financial advice from AI"""
    if not st.session_state.token:
        return "Please log in to get financial advice."
        
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{API_URL}/chat/secure-advice",
            headers=headers,
            json={"prompt": prompt}
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Failed to get advice: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def create_portfolio(portfolio_data):
    """Create user portfolio"""
    if not st.session_state.token:
        return False
        
    try:
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{API_URL}/portfolio/secure/add_portfolio",
            headers=headers,
            json=portfolio_data
        )
        
        if response.status_code == 200:
            st.success("Portfolio created successfully!")
            return True
        else:
            st.error(f"Failed to create portfolio: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error creating portfolio: {str(e)}")
        return False

def show_portfolio_visualization(portfolio):
    """Show portfolio visualization"""
    if not portfolio:
        st.warning("No portfolio data available")
        return
        
    # Create a dataframe for the portfolio
    portfolio_dict = {
        'Asset': ['Equity', 'Cash', 'Fixed Deposits', 'Debt', 'Real Estate', 'Bonds', 'Crypto'],
        'Amount': [
            portfolio.get('equity_amt', 0),
            portfolio.get('cash_amt', 0),
            portfolio.get('fd_amt', 0),
            portfolio.get('debt_amt', 0),
            portfolio.get('real_estate_amt', 0),
            portfolio.get('bonds_amt', 0),
            portfolio.get('crypto_amt', 0)
        ]
    }
    
    df = pd.DataFrame(portfolio_dict)
    
    # Calculate total portfolio value
    total = sum(portfolio_dict['Amount'])
    
    # Create a pie chart
    fig = px.pie(
        df,
        values='Amount',
        names='Asset',
        title=f'Portfolio Allocation (Total: ${total:,.2f})',
        hole=0.3
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Main app layout
st.title("FinAdvisor - Your Personal Financial Advisor")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigate", ["Login", "Dashboard", "Portfolio", "Financial Advice"])

if page == "Login":
    st.header("Login")
    
    # Registration section
    with st.expander("New user? Register here"):
        with st.form("register_form"):
            reg_username = st.text_input("Username", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_age = st.number_input("Age", min_value=18, max_value=100, key="reg_age")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                try:
                    response = requests.post(
                        f"{API_URL}/user/create_profile/",
                        json={
                            "username": reg_username,
                            "email": reg_email,
                            "password": reg_password,
                            "name": reg_name,
                            "age": reg_age
                        }
                    )
                    
                    if response.status_code in (200, 201):
                        st.success("Registration successful! Please log in.")
                    else:
                        st.error(f"Registration failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            success = login(username, password)
            if success:
                st.success("Login successful!")
                st.rerun()  # Rerun the app to update the UI

elif not st.session_state.token:
    st.warning("Please login first")
    st.button("Go to Login", on_click=lambda: st.session_state.update({"page": "Login"}))

elif page == "Dashboard":
    st.header("Dashboard")
    
    user_data = st.session_state.user_data
    portfolio = get_portfolio()
    
    if user_data:
        st.subheader(f"Welcome, {user_data.get('name', 'User')}!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"Username: {user_data.get('username')}")
            st.info(f"Email: {user_data.get('email')}")
            st.info(f"Age: {user_data.get('age')}")
        
        with col2:
            if portfolio:
                total_assets = sum([
                    portfolio.get('equity_amt', 0),
                    portfolio.get('cash_amt', 0),
                    portfolio.get('fd_amt', 0),
                    portfolio.get('debt_amt', 0),
                    portfolio.get('real_estate_amt', 0),
                    portfolio.get('bonds_amt', 0),
                    portfolio.get('crypto_amt', 0)
                ])
                
                st.metric("Total Portfolio Value", f"${total_assets:,.2f}")
            else:
                st.warning("No portfolio data available")
                st.button("Create Portfolio", on_click=lambda: st.session_state.update({"_page": "Portfolio"}))
        
        if portfolio:
            show_portfolio_visualization(portfolio)
    else:
        st.warning("User profile data not available")

elif page == "Portfolio":
    st.header("Portfolio Management")
    
    portfolio = get_portfolio()
    
    if portfolio:
        st.subheader("Your Current Portfolio")
        show_portfolio_visualization(portfolio)
        
        with st.expander("Update Portfolio"):
            equity = st.number_input("Equity Amount", min_value=0.0, value=float(portfolio.get('equity_amt', 0)))
            cash = st.number_input("Cash Amount", min_value=0.0, value=float(portfolio.get('cash_amt', 0)))
            fd = st.number_input("Fixed Deposits", min_value=0.0, value=float(portfolio.get('fd_amt', 0)))
            debt = st.number_input("Debt Amount", min_value=0.0, value=float(portfolio.get('debt_amt', 0)))
            real_estate = st.number_input("Real Estate Amount", min_value=0.0, value=float(portfolio.get('real_estate_amt', 0)))
            bonds = st.number_input("Bonds Amount", min_value=0.0, value=float(portfolio.get('bonds_amt', 0)))
            crypto = st.number_input("Crypto Amount", min_value=0.0, value=float(portfolio.get('crypto_amt', 0)))
            
            if st.button("Update Portfolio"):
                headers = {
                    "Authorization": f"Bearer {st.session_state.token}",
                    "Content-Type": "application/json"
                }
                
                try:
                    response = requests.put(
                        f"{API_URL}/portfolio/secure/update_portfolio",
                        headers=headers,
                        json={
                            "equity_amt": equity,
                            "cash_amt": cash,
                            "fd_amt": fd,
                            "debt_amt": debt,
                            "real_estate_amt": real_estate,
                            "bonds_amt": bonds,
                            "crypto_amt": crypto
                        }
                    )
                    
                    if response.status_code == 200:
                        st.success("Portfolio updated successfully!")
                        st.experimental_rerun()
                    else:
                        st.error(f"Failed to update portfolio: {response.text}")
                except Exception as e:
                    st.error(f"Error updating portfolio: {str(e)}")
    else:
        st.info("You don't have a portfolio yet. Let's create one!")
        
        equity = st.number_input("Equity Amount", min_value=0.0)
        cash = st.number_input("Cash Amount", min_value=0.0)
        fd = st.number_input("Fixed Deposits", min_value=0.0)
        debt = st.number_input("Debt Amount", min_value=0.0)
        real_estate = st.number_input("Real Estate Amount", min_value=0.0)
        bonds = st.number_input("Bonds Amount", min_value=0.0)
        crypto = st.number_input("Crypto Amount", min_value=0.0)
        
        if st.button("Create Portfolio"):
            portfolio_data = {
                "equity_amt": equity,
                "cash_amt": cash,
                "fd_amt": fd,
                "debt_amt": debt,
                "real_estate_amt": real_estate,
                "bonds_amt": bonds,
                "crypto_amt": crypto
            }
            
            success = create_portfolio(portfolio_data)
            if success:
                st.experimental_rerun()

elif page == "Financial Advice":
    st.header("AI Financial Advisor")
    
    st.write("Ask our AI for personalized financial advice based on your portfolio and financial goals.")
    
    prompt = st.text_area("Your Question:", height=100, placeholder="Example: How should I invest $10,000 given my current portfolio?")
    
    if st.button("Get Advice"):
        if prompt:
            with st.spinner("Getting advice..."):
                response = get_financial_advice(prompt)
                st.markdown(response)
        else:
            st.warning("Please enter a question.")
    
    st.divider()
    st.subheader("Example Questions")
    example_questions = [
        "How should I diversify my portfolio?",
        "What percentage of my income should I save each month?",
        "Should I invest more in stocks or bonds given the current market?",
        "How can I plan for retirement given my current savings?",
        "What are tax-efficient investment strategies for someone in my position?"
    ]
    
    for question in example_questions:
        if st.button(question):
            with st.spinner("Getting advice..."):
                response = get_financial_advice(question)
                st.markdown(response)

# Add logout button to sidebar
if st.session_state.token:
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user_data = None
        st.rerun()