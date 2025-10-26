# src/utils/newsapi_utils.py
import json
import time
import requests
from itertools import cycle
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime, timedelta
from src.constants import NEWS_API_KEY
from src.logger import logging

NEWS_API_KEYS = NEWS_API_KEY
if not NEWS_API_KEYS or NEWS_API_KEYS == '':
    raise ValueError("No NEWS_API_KEYS found in env")

key_cycle = cycle(NEWS_API_KEYS)

def get_news_api_key():
    return next(key_cycle)

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=['GET'])
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


def build_query(startup_name, helping_words):
    base_terms = [
        f'"{startup_name}"',
        f'"{startup_name}" startup',
        f'"{startup_name}" company',
        f'"{startup_name}" India'
    ]
    if helping_words:
        if isinstance(helping_words, str):
            helping_words = json.loads(helping_words) if helping_words.strip().startswith('[') else helping_words.split(',')
        base_terms.extend([f'"{word.strip()}"' for word in helping_words])
    return " OR ".join(base_terms)


def fetch_articles(startup_name, helping_words, days):
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    all_articles = []
    page = 1

    while True:
        api_key = get_news_api_key()
        params = {
            "q": build_query(startup_name, helping_words),
            "from": from_date,
            "to": to_date,
            "sortBy": "publishedAt",
            "apiKey": api_key,
            "language": "en",
            "pageSize": 100,
            "page": page
        }

        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.warning(f"Request failed for {startup_name} (page {page}): {e}")
            break

        data = response.json()
        if not data.get("articles"):
            break

        all_articles.extend(data["articles"])
        logging.info(f"Fetched {len(data['articles'])} from page {page}")

        if len(data["articles"]) < 100:
            break

        page += 1
        time.sleep(1.2)

    return all_articles
