import os
from dotenv import load_dotenv

load_dotenv()

# --- File Paths ---
FOUNDERS_FILE = "../data/founders1.csv"
INVESTORS_FILE = "../data/investors1.csv"

# --- Gemini API ---
API_KEY = os.getenv("GEMINI_API_KEY")
GENERATIVE_MODEL_NAME = "gemini-1.5-flash-latest" # or "gemini-pro"

# --- Rate Limiting & Retry ---
MAX_CONCURRENT_REQUESTS = 5 
RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY_SECONDS = 5 

# --- Streamlit App ---
DEFAULT_TOP_N = 5
APP_TITLE = "AI Founder-Investor Matcher"

# --- Logging ---
LOG_LEVEL = "INFO" # e.g., DEBUG, INFO, WARNING, ERROR