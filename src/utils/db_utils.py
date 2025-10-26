# src/utils/db_utils.py
import json
import psycopg2
from src.constants import DB_URL
from datetime import datetime
from src.database import db_connection
from src.logger import logging


def get_connection():
    """Safely create a new DB connection."""
    try:
        DATABASE_URL = DB_URL
        if not DB_URL:
            raise ValueError("Database URL not found. Please set DB_URL in environment or constants.")

        conn = psycopg2.connect(DATABASE_URL)
        # cur = conn.cursor()
        logging.info('db connected')
        return conn
    except Exception as e:
        logging.error(f"Failed to create DB connection: {e}")
        raise


def fetch_existing_urls():
    """Fetch URLs from Articles table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT url FROM "Articles"')
            urls = {row[0] for row in cur.fetchall() if row[0]}
        logging.info(f"Fetched {len(urls)} existing URLs from DB")
        return urls
    finally:
        conn.close()


def fetch_startups():
    """Fetch startup id, name, and keywords."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, COALESCE("findingKeywords",\'{}\') FROM "Startups"')
            startups = cur.fetchall()
        return startups
    finally:
        conn.close()


def fetch_startup_id_from_articles():
    """Fetch distinct startup IDs from Articles."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT DISTINCT "startupId" FROM "Articles"')
            startup_saved = cur.fetchall()
        return startup_saved
    finally:
        conn.close()


def fetch_startup_id_from_startupss():
    """Fetch all startup IDs from Startups."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "id" FROM "Startups"')
            startup_saved = cur.fetchall()
        return startup_saved
    finally:
        conn.close()


def fetch_missing_startups():
    """Fetch startups that are not yet present in Articles."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.name, COALESCE(s."findingKeywords", '{}')
                FROM "Startups" s 
                WHERE s.id NOT IN (SELECT "startupId" FROM "Articles")
            """)
            missing = cur.fetchall()
        logging.info('Fetched missing startups')
        return missing
    finally:
        conn.close()
