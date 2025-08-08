import os
import psycopg2
import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

def setup_database():
    """Ensures the 'briefs' table exists, same as in the main scraper."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id SERIAL PRIMARY KEY,
            content TEXT UNIQUE NOT NULL,
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database setup checked/complete.")

def insert_test_data():
    """Connects to the database and inserts a single test entry."""
    if not DATABASE_URL:
        raise Exception("Fatal: DATABASE_URL environment variable is not set.")

    # A unique string to prove this specific test run worked.
    test_string = f"Test successful from GitHub Actions at {datetime.datetime.utcnow().isoformat()}"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print(f"Attempting to insert test data: '{test_string}'")
        cur.execute("INSERT INTO briefs (content) VALUES (%s);", (test_string,))
        conn.commit()
        print("Successfully inserted test data into the 'briefs' table.")
    except Exception as e:
        print(f"Failed to insert test data. Error: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("Running Database Connection Test")
    setup_database()
    insert_test_data()
    print("Test Finished")