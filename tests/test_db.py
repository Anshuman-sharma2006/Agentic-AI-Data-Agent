import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# 1. Connect to Neon PostgreSQL
conn = psycopg2.connect(
    os.getenv("DATABASE_URL")
)

print("Connected to Neon!")

# 2. Create a cursor(lets you send SQL and receive results through that connection)-kind of bridge between your code and the database
cursor = conn.cursor()

# 3. Send SQL command to PostgreSQL
cursor.execute("SELECT version();")

# 4. Get the result
print(cursor.fetchone())

# 5. Close cursor
cursor.close()

# 6. Close database connection
conn.close()

