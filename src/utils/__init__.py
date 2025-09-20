import numpy as np
import json
import uuid
from src.database import db_connection
from datetime import datetime, timedelta
from src.constants import *
import requests


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
    cur = conn.cursor()
    cur.execute('SELECT id,name FROM "Startups"')
    startups = cur.fetchall()
    cur.close()
    return startups

def unique_id(input_file,output_file):
    # Load existing JSON
    with open(input_file, "r") as f:
        data = json.load(f)

    for startup in data:
        if "id" not in startup or not startup["id"]:
            startup["id"] = str(uuid.uuid4()) 

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print("UUIDs added successfully.")

def initial_fetch(startup_name):
    to_date = datetime.today().date()
    from_date = to_date - timedelta(days=30)
    params = {
        "q": startup_name,
        "from": str(from_date),
        "to": str(to_date),
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 100
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    return data.get("articles", [])