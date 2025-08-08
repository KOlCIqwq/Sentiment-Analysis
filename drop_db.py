import os
import psycopg2

if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    conn = None
    cur = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Attempting to drop 'briefs' table...")
        cur.execute("DROP TABLE IF EXISTS briefs;")
        
        conn.commit()
        
        print("✅ Table 'briefs' successfully dropped.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Connection closed.")