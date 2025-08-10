import os
import psycopg2
from flask import Flask, render_template

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    articles = []
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        # Fetch the 50 most recent, PROCESSED articles
        cur.execute(
            """
            SELECT content, subject_company, sentiment, scraped_at
            FROM briefs 
            WHERE sentiment IS NOT NULL 
            ORDER BY scraped_at DESC 
            LIMIT 50
            """
        )
        # Fetchall returns a list of tuples
        articles = cur.fetchall()
    except Exception as e:
        print(f"Database query failed: {e}")
    finally:
        cur.close()
        conn.close()
    
    return render_template('index.html', articles=articles)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))