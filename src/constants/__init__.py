from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("DB_URI")

BASE_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.getenv("NEWS_API","").split(",")

hf_token = os.getenv("HF_TOKEN")