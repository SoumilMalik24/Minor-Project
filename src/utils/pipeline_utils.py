# =========================================================
# src/utils/pipeline_utils.py
# =========================================================
# Handles the orchestration of startup-wise article fetching,
# deduplication, sentiment scoring, truncation, and DB storage.
# =========================================================

import uuid
from src.logger import logging
from src.utils.db_utils import get_connection
from src.utils.newsapi_utils import fetch_articles
from src.utils.cache_utils import check_duplicacy
from src.utils.sentiment_utils import sentiment_score_batch
from src.utils.text_utils import merge_text, truncate_content


# =========================================================
# CORE PIPELINE FUNCTION
# =========================================================
def process_and_store_articles(startup_id, startup_name, helping_words, days):
    """
    Fetches articles for a startup (1-day or 30-day range),
    removes duplicates, scores sentiments, truncates content,
    and inserts data into the Articles table.
    """

    logging.info(f"📰 Starting {days}-day article processing for {startup_name}")

    # 1️⃣ Fetch articles from NewsAPI
    articles = fetch_articles(startup_name, helping_words, days)
    if not articles:
        logging.info(f"No articles found for {startup_name}")
        return

    # 2️⃣ Deduplicate using cache
    new_articles = check_duplicacy(articles)
    if not new_articles:
        logging.info(f"No new articles after deduplication for {startup_name}")
        return

    # 3️⃣ Merge and clean article text
    contents, valid_articles = [], []
    for article in new_articles:
        content = merge_text(article.get("description"), article.get("content"))
        if not content or len(content) < 30:
            continue
        contents.append(content)
        valid_articles.append(article)

    if not contents:
        logging.info(f"No valid article content for {startup_name}")
        return

    # 4️⃣ Sentiment analysis using FinBERT
    results = sentiment_score_batch(contents)
    if not results:
        logging.warning(f"Sentiment scoring failed for {startup_name}")
        return

    # 5️⃣ Prepare records for insertion
    batch = []
    for article, (sentiment, score), content in zip(valid_articles, results, contents):
        truncated = truncate_content(content)
        batch.append((
            str(uuid.uuid4()),                # id
            truncated,                        # content (≤ 300 chars)
            article.get("publishedAt"),       # publishedAt
            sentiment,                        # sentiment label
            score,                            # sentiment score
            startup_id,                       # startupId (FK)
            article.get("title") or "untitled",  # title
            article.get("url")                # url
        ))

    if not batch:
        logging.info(f"No valid batch to insert for {startup_name}")
        return

    # 6️⃣ Insert into database
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO "Articles" 
                (id, content, "publishedAt", sentiment, "sentimentScore", "startupId", title, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
        conn.commit()
        logging.info(f"✅ Inserted {len(batch)} new articles for {startup_name}")
    except Exception as e:
        logging.error(f"❌ Failed to insert articles for {startup_name}: {e}")
        conn.rollback()
    finally:
        conn.close()
        logging.info(f"Closed DB connection for {startup_name}")


# =========================================================
# WRAPPERS (for easy pipeline calls)
# =========================================================
def process_and_store_initial_articles(startup_id, startup_name, helping_words):
    """
    Handles 30-day article fetching for startups that do NOT yet exist in the Articles table.
    """
    try:
        process_and_store_articles(startup_id, startup_name, helping_words, days=30)
    except Exception as e:
        logging.error(f"[INITIAL] Pipeline failed for {startup_name}: {e}")


def process_and_store_daily_articles(startup_id, startup_name, helping_words):
    """
    Handles 1-day article fetching for startups that already exist in the Articles table.
    """
    try:
        process_and_store_articles(startup_id, startup_name, helping_words, days=1)
    except Exception as e:
        logging.error(f"[DAILY] Pipeline failed for {startup_name}: {e}")
