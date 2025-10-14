import numpy as np
import json
import uuid
import requests
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime, timedelta
import time
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.database import db_connection
from src.constants import *
from src.logger import logging
from itertools import cycle


# =========================================================
# Global URL cache (for duplicate detection)
# =========================================================
def reset_url_cache():
    """
    Clears the in-memory URL cache before each pipeline run.
    Prevents old URLs from previous runs causing false duplicates.
    """
    global _EXISTING_URLS_CACHE, _EXISTING_URLS_CACHE_TS
    _EXISTING_URLS_CACHE = set()
    _EXISTING_URLS_CACHE_TS = 0
    logging.info("URL duplicate cache reset.")


def get_connection():
    """
    Safely create a new database connection for each operation.
    Ensures that every function works with its own isolated connection.
    """
    try:
        return db_connection()
    except Exception as e:
        logging.error(f"Failed to create DB connection: {e}")
        raise


# =========================================================
# URL Cache Helpers
# =========================================================
def fetch_existing_urls():
    global _EXISTING_URLS_CACHE, _EXISTING_URLS_CACHE_TS

    if _EXISTING_URLS_CACHE:
        return _EXISTING_URLS_CACHE

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT url FROM "Articles"')
            urls = {row[0] for row in cur.fetchall() if row[0]}
        _EXISTING_URLS_CACHE = urls
        _EXISTING_URLS_CACHE_TS = datetime.now().timestamp()
        logging.info(f"Fetched {len(urls)} existing URLs from DB")
    finally:
        conn.close()

    return _EXISTING_URLS_CACHE


# =========================================================
# Startup Fetch Helpers
# =========================================================
def fetch_startups():
    logging.info("Retrieving id and name from Startups")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, COALESCE("findingKeywords",\'{}\') FROM "Startups"')
            startups = cur.fetchall()
        return startups
    finally:
        conn.close()


def fetch_startup_id_from_articles():
    logging.info("Fetching startup IDs from Articles")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT DISTINCT "startupId" FROM "Articles"')
            startup_saved = cur.fetchall()
        return startup_saved
    finally:
        conn.close()


def fetch_startup_id_from_startupss():
    logging.info('Fetching startup info from Startups DB')
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "id" FROM "Startups"')
            startup_saved = cur.fetchall()
        return startup_saved
    finally:
        conn.close()


def fetch_missing_startups():
    logging.info('Fetching missing startups from Articles DB')
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.name, COALESCE(s."findingKeywords", '{}')
                FROM "Startups" s 
                WHERE s.id NOT IN (SELECT "startupId" FROM "Articles")
            """)
            missing = cur.fetchall()
        logging.info('Fetching DONE for missing startups')
        return missing
    finally:
        conn.close()
# =========================================================
# News API query building
# =========================================================
def  build_query(startup_name, helping_words):
    base_terms = [
        f'"{startup_name}"'
        f'"{startup_name}" startup'
        f'"{startup_name}" company'
        f'"{startup_name}" India'
    ]
    if helping_words:
        if isinstance(helping_words,str):
            helping_words = json.loads(helping_words) if helping_words.strip().startswith('[') else helping_words.split(',')
        base_terms.extend([f'"{word.strip()}"' for word in helping_words])

        return " OR ".join(base_terms)

# =========================================================
# News API setup with retry and timeout handling
# =========================================================
NEWS_API_KEYS = NEWS_API_KEY

if not NEWS_API_KEYS or NEWS_API_KEYS=='':
    raise ValueError("no NEWS_API_KEYS found in the env")

key_cycle = cycle(NEWS_API_KEYS)

def get_news_api_key():
    return next(key_cycle)

session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=['GET']
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


def initial_fetch_articles(startup_name, helping_words):
    logging.info(f"Fetching 30-day news for {startup_name}")
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    all_articles = []
    page = 1

    while True:
        api_key = get_news_api_key()
        params = {
            "q": build_query(startup_name, helping_words),
            "from": str(from_date),
            "to": str(to_date),
            "sortBy": "publishedAt",
            "apiKey": api_key,
            "language": "en",
            "pageSize": 100,
            "page": page
        }

        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed for {startup_name} (page {page}): {e}")
            break

        data = response.json()
        if "articles" not in data or not data["articles"]:
            break

        all_articles.extend(data["articles"])
        logging.info(f"Fetched {len(data['articles'])} articles from page {page}")

        if len(data["articles"]) < 100:
            break

        page += 1
        time.sleep(1.2)

    return all_articles


def repeat_fetch_articles(startup_name, helping_words):
    logging.info(f"Fetching 1-day news for {startup_name}")
    from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    all_articles = []
    page = 1

    while True:
        api_key = get_news_api_key()
        params = {
            "q": build_query(startup_name, helping_words),
            "from": str(from_date),
            "to": str(to_date),
            "sortBy": "publishedAt",
            "apiKey": api_key,
            "language": "en",
            "pageSize": 100,
            "page": page
        }

        try:
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed for {startup_name} (page {page}): {e}")
            break

        data = response.json()
        if "articles" not in data or not data["articles"]:
            break

        all_articles.extend(data["articles"])
        logging.info(f"Fetched {len(data['articles'])} articles from page {page}")

        if len(data["articles"]) < 100:
            break

        page += 1
        time.sleep(1.2)

    return all_articles


# =========================================================
# Hugging Face Model Setup
# =========================================================
MODEL_ID = "Soumil24/finbert-custom"
token = hf_token

try:
    logging.info(f"Loading FinBERT model from Hugging Face: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_auth_token=token)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, use_auth_token=token)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    logging.info(f"FinBERT model loaded successfully on {device.upper()}")
except Exception as e:
    logging.error(f"Failed to load FinBERT model: {e}")
    raise


# =========================================================
# Sentiment Scoring
# =========================================================
def sentiment_score(text):
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, padding=True, max_length=256
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

    labels = ["negative", "neutral", "positive"]
    weights = {"negative": -1, "neutral": 0, "positive": 1}
    sentiment = labels[int(probs.argmax())]
    score = float(sum(probs[i] * weights[labels[i]] for i in range(len(probs))))
    return sentiment, score


def sentiment_score_batch(texts):
    if not texts:
        return []

    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()

    labels = ["negative", "neutral", "positive"]
    weights = {"negative": -1, "neutral": 0, "positive": 1}

    results = []
    for prob in probs:
        sentiment = labels[int(prob.argmax())]
        score = float(sum(prob[i] * weights[labels[i]] for i in range(len(prob))))
        results.append((sentiment, score))

    return results


# =========================================================
# Duplicate Article Check
# =========================================================
def check_duplicacy(articles):
    logging.info('Checking for duplicate articles')
    global _EXISTING_URLS_CACHE
    existing_urls = fetch_existing_urls()

    new_articles = [a for a in articles if a.get('url') and a['url'] not in existing_urls]
    logging.info(f"Found {len(new_articles)} new articles after removing duplicates using cache")

    try:
        new_urls = {a['url'] for a in new_articles if a.get('url')}
        _EXISTING_URLS_CACHE.update(new_urls)
        logging.info(f"Updated existing URLs cache with {len(new_urls)} new URLs")
    except Exception as e:
        logging.warning(f"Failed to update the URL cache: {e}")

    return new_articles


# =========================================================
# Article Processing & Storage
# =========================================================
def process_and_store_initial_articles(startup_id, startup_name, helping_words):
    articles = initial_fetch_articles(startup_name,helping_words)
    new_articles = check_duplicacy(articles)
    logging.info("Articles fetched and checked for duplicacy")

    contents = []
    valid_articles = []
    for article in new_articles:
        desc = article.get("description") or ""
        cont = article.get("content") or ""
        content = (desc + ". " + cont).strip()
        if not content or len(content) < 30:
            continue
        contents.append(content)
        valid_articles.append(article)

    if not contents:
        logging.info(f"No valid contents for {startup_name}")
        return

    results = sentiment_score_batch(contents)
    batch = []

    if len(content) > 300:
        truncated_content = content[:300].rsplit(' ', 1)[0] + "..."
    else:
        truncated_content = content

    for article, (sentiment, score) in zip(valid_articles, results):
        content = article.get("content") or article.get("description")
        batch.append((
            str(uuid.uuid4()),
            truncated_content,
            article.get("publishedAt"),
            sentiment,
            score,
            startup_id,
            article.get("title") or "untitled",
            article.get("url")
        ))

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO "Articles" 
                (id, content, "publishedAt", sentiment, "sentimentScores", "startupId", title, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
        conn.commit()
    finally:
        conn.close()

    logging.info(f"Inserted {len(new_articles)} articles for {startup_name}")


def process_and_store_daily_articles(startup_id, startup_name, helping_words):
    articles = repeat_fetch_articles(startup_name,helping_words)
    new_articles = check_duplicacy(articles)
    logging.info("Articles fetched and checked for duplicacy")

    contents = []
    valid_articles = []
    for article in new_articles:
        desc = article.get("description") or ""
        cont = article.get("content") or ""
        content = (desc + ". " + cont).strip()
        if not content or len(content) < 30:
            continue
        contents.append(content)
        valid_articles.append(article)

    if not contents:
        logging.info(f"No valid contents for {startup_name}")
        return

    results = sentiment_score_batch(contents)
    batch = []
    if len(content) > 300:
        truncated_content = content[:300].rsplit(' ', 1)[0] + "..."
    else:
        truncated_content = content

    for article, (sentiment, score) in zip(valid_articles, results):
        content = article.get("content") or article.get("description")
        batch.append((
            str(uuid.uuid4()),
            truncated_content,
            article.get("publishedAt"),
            sentiment,
            score,
            startup_id,
            article.get("title") or "untitled",
            article.get("url")
        ))

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO "Articles" 
                (id, content, "publishedAt", sentiment, "sentimentScores", "startupId", title, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
        conn.commit()
    finally:
        conn.close()

    logging.info(f"Inserted {len(new_articles)} articles for {startup_name}")
