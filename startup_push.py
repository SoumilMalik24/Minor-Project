import json
from src.database import db_connection

# Get connection and cursor
conn = db_connection()
cur = conn.cursor()

with open("startups_id.json", "r") as f:
    data = json.load(f)


stp = [(
    startup.get("id"),
    startup.get("description"),
    startup.get("keywords"),
    startup.get("name"),
    startup.get("sector")) for startup in data]

cur.executemany("""
    INSERT INTO "Startups" (id, description, "findingKeywords", name, sector)
    VALUES (%s, %s, %s, %s, %s)
""",stp )


# Save changes
conn.commit()

# Close
cur.close()
conn.close()

print("Startups inserted successfully!")
