import streamlit as st
import requests
import json

def show_error(message):
    """Display an error message"""
    st.error(message)

def show_success(message):
    """Display a success message"""
    st.success(message)

def load_lottie(url):
    """Load a Lottie animation from URL"""
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception:
        return None

def load_css(file_name):
    """Load CSS from a file and inject it"""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Create a default CSS if file doesn't exist
        with open("style.css", "w") as f:
            f.write("""
            /* Custom styling for FinAdvisor */
            .stApp {
                background-color: #f5f7fa;
            }
            
            .stSidebar {
                background-color: #ffffff;
                border-right: 1px solid #eaeaea;
            }
            
            h1, h2, h3 {
                color: #1a3c6e;
            }
            
            .stButton>button {
                border-radius: 6px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
            
            /* Chat styling */
            .chat-message {
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            
            .user-message {
                background-color: #e1f0ff;
                margin-left: 2rem;
            }
            
            .assistant-message {
                background-color: #f0f2f5;
                margin-right: 2rem;
            }
            """)
        
        st.markdown("""
        <style>
        /* Custom styling for FinAdvisor */
        .stApp {
            background-color: #f5f7fa;
        }
        
        .stSidebar {
            background-color: #ffffff;
            border-right: 1px solid #eaeaea;
        }
        
        h1, h2, h3 {
            color: #1a3c6e;
        }
        
        .stButton>button {
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        /* Chat styling */
        .chat-message {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .user-message {
            background-color: #e1f0ff;
            margin-left: 2rem;
        }
        
        .assistant-message {
            background-color: #f0f2f5;
            margin-right: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)