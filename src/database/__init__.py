import psycopg2
from src.constants import *


def db_connection():
    DATABASE_URL = DB_URL
    conn = psycopg2.connect(DATABASE_URL)
    # cur = conn.cursor()
    return conn