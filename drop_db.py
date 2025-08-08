import os
import psycopg2

if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Dropping 'briefs' table if it exists...")
        cur.execute("DROP TABLE IF EXISTS briefs;")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
