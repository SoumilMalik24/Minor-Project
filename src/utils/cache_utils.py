# src/utils/cache_utils.py
from datetime import datetime
from src.utils.db_utils import fetch_existing_urls
from src.logger import logging

_EXISTING_URLS_CACHE = set()
_EXISTING_URLS_CACHE_TS = 0


def reset_url_cache():
    """Clears in-memory cache to avoid false duplicates."""
    global _EXISTING_URLS_CACHE, _EXISTING_URLS_CACHE_TS
    _EXISTING_URLS_CACHE = set()
    _EXISTING_URLS_CACHE_TS = 0
    logging.info("URL duplicate cache reset.")


def fetch_existing_urls_cache():
    """Fetch URLs and cache them."""
    global _EXISTING_URLS_CACHE, _EXISTING_URLS_CACHE_TS
    if _EXISTING_URLS_CACHE:
        return _EXISTING_URLS_CACHE
    urls = fetch_existing_urls()
    _EXISTING_URLS_CACHE = urls
    _EXISTING_URLS_CACHE_TS = datetime.now().timestamp()
    logging.info(f"Cached {len(urls)} URLs from DB")
    return _EXISTING_URLS_CACHE


def check_duplicacy(articles):
    """Filter out duplicate articles using cache."""
    global _EXISTING_URLS_CACHE
    existing_urls = fetch_existing_urls_cache()
    new_articles = [a for a in articles if a.get('url') and a['url'] not in existing_urls]
    new_urls = {a['url'] for a in new_articles if a.get('url')}
    _EXISTING_URLS_CACHE.update(new_urls)
    logging.info(f"Removed duplicates; {len(new_articles)} new articles remain.")
    return new_articles