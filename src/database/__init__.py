import psycopg2
from src.constants import *
from src.logger import logging


def db_connection():
    DATABASE_URL = DB_URL
    conn = psycopg2.connect(DATABASE_URL)
    # cur = conn.cursor()
    logging.info('db connected')
    return conn