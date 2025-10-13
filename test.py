from src.database import db_connection

# Clear Articles table
conn = db_connection()  
cur = conn.cursor()
cur.execute('''
TRUNCATE TABLE "Articles" RESTART IDENTITY;
''')
conn.commit()
cur.close()
conn.close()