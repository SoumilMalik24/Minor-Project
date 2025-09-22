import numpy as np
import json
import uuid
from src.database import db_connection
from datetime import datetime, timedelta
from src.constants import *
import requests
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.logger import logging


conn = db_connection()

def fetch_urls():
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM "Articles"')
    Number = cur.fetchall()
    if Number[0][0]==0:
        return "No Articles" 
    else:
        cur.execute('SELECT url FROM "Articles"')
        urls = cur.fetchall()
        cur.close()
        return np.array(urls).flatten()



def fetch_startups():
    logging.info("retrieving id and name from Startups")
    cur = conn.cursor()
    cur.execute('SELECT id,name FROM "Startups"')
    startups = cur.fetchall()
    cur.close()
    return startups

def unique_id(input_file):
    # Load existing JSON
    with open(input_file, "r") as f:
        data = json.load(f)

    for startup in data:
        if "id" not in startup or not startup["id"]:
            startup["id"] = str(uuid.uuid4()) 

    with open(input_file, "w") as f:
        json.dump(data, f, indent=2)

    print("UUIDs added successfully.")


NEWS_API = NEWS_API_KEY

def initial_fetch_articles(startup_name):
    logging.info("fetch started for new startup")
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    all_articles = []
    page = 1
    
    while True:
        params = {
            "q": startup_name,
            "from": str(from_date),
            "to": str(to_date),
            "sortBy": "publishedAt",
            "apiKey": NEWS_API,
            "language": "en",
            "pageSize": 100,   
            "page": page       
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "articles" not in data or not data["articles"]:
            break  # no more results

        all_articles.extend(data["articles"])
        logging.info(f"Fetched {len(data['articles'])} articles from page {page}")

        if len(data["articles"]) < 100:
            break  # last page reached

        page += 1

    return all_articles

def repeat_fetch_articles(startup_name):
    logging.info("fetching daily news for old startups")
    from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    all_articles = []
    page = 1
    
    while True:
        params = {
            "q": startup_name,
            "from": str(from_date),
            "to": str(to_date),
            "sortBy": "publishedAt",
            "apiKey": NEWS_API,
            "language": "en",
            "pageSize": 100,   
            "page": page       
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "articles" not in data or not data["articles"]:
            break  # no more results

        all_articles.extend(data["articles"])
        logging.info(f"Fetched {len(data['articles'])} articles from page {page}")

        if len(data["articles"]) < 100:
            break  # last page reached

        page += 1

    return all_articles

def fetch_startup_id_from_articles():
    logging.info("fetching startup id from articles")
    cur = conn.cursor()
    cur.execute('SELECT "startupId" FROM "Articles"')
    startup_saved = cur.fetchall()
    cur.close()
    return startup_saved

def fetch_startup_id_from_startupss():
    logging.info('fetching startup info from Startups db')
    cur = conn.cursor()
    cur.execute('SELECT "id" FROM "Startups"')
    startup_saved = cur.fetchall()
    cur.close()
    return startup_saved

def fetch_missing_startups():
    logging.info('fetching missing startups from Articles db')
    cur = conn.cursor()
    cur.execute("""SELECT s.id,s.name 
                FROM "Startups"s 
                WHERE s.id NOT IN(SELECT "startupId" FROM "Articles" ) 
                """)

    missing = cur.fetchall()
    cur.close()
    logging.info('fetching DONE for missing startups from Articles db')
    return missing


def sentiment_score(text: str):
    logging.info('Sentiment Analysis started')
    MODEL_PATH = r"Soumil24/finbert-custom"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()

    """Predict sentiment and return (label, score in [-1, 1])"""
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True
    ).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()[0]

    # Adjust these if your model has different class order
    sentiment_values = {"negative": -1, "neutral": 0, "positive": 1}
    id2label = {0: "negative", 1: "neutral", 2: "positive"}

    score = float(sum(probs[i] * sentiment_values[id2label[i]] for i in range(len(probs))))
    predicted_label = id2label[int(probs.argmax())]

    logging.info('sentiment analysis done')
    return predicted_label, score

def check_duplicacy(articles):
    logging.info('checking for duplicate articles')
    cur = conn.cursor()

    cur.execute("SELECT url FROM \"Articles\"")
    article_url = {row[0] for row in cur.fetchall()}

    new_articles = [a for a in articles if a.get('url') not in article_url]
    logging.info('checking DONE for duplicate articles')

    return new_articles
    

def process_and_store_initial_articles(startup_id, startup_name):
    articles = initial_fetch_articles(startup_name)
    new_articles = check_duplicacy(articles)
    logging.info("articles fetched and checked for duplicacy")
    for article in new_articles:
        content = article.get("content") or article.get("description")
        
        if not content:  # skip empty ones
            continue
        
        sentiment, score = sentiment_score(content)
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "Articles" 
                (id, content, "publishedAt", sentiment, "sentimentScores", "startupId", title, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                (content[:300] if content else None),
                article.get("publishedAt"),
                sentiment,
                score,
                startup_id,
                article.get("title") or "untitled",
                article.get("url")
            ))
    conn.commit()
    logging.info(f"Inserted {len(new_articles)} articles for {startup_name}")


def process_and_store_daily_articles(startup_id, startup_name):
    articles = repeat_fetch_articles(startup_name)
    new_articles = check_duplicacy(articles)
    logging.info("articles fetched and checked for duplicacy")
    for article in new_articles:
        content = article.get("content") or article.get("description")
        
        if not content:  # skip empty ones
            continue
        
        sentiment, score = sentiment_score(content)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "Articles" 
                (id, content, "publishedAt", sentiment, "sentimentScores", "startupId", title, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                (content[:300] if content else None),
                article.get("publishedAt"),
                sentiment,
                score,
                startup_id,
                article.get("title") or "untitled",
                article.get("url")
            ))
    conn.commit()
    logging.info(f"Inserted {len(new_articles)} articles for {startup_name}")