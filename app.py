# app.py on Render - The Viewer
import os
import psycopg2
from flask import Flask, render_template, jsonify 

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    return render_template('index.html')

def get_todays_articles():
    """Helper function to fetch all processed articles published today (UTC)."""
    articles = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Use the 'scraped_at' column to filter by date.
                cur.execute(
                    """
                    SELECT content, subject_company, sentiment, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                      AND scraped_at >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
                    ORDER BY scraped_at DESC;
                    """
                )
                articles = cur.fetchall()
    except Exception as e:
        print(f"Database query failed: {e}")
    return articles

@app.route('/api/articles')
def api_articles():
    db_articles = get_todays_articles()
    
    articles_as_dicts = []
    for article in db_articles:
        articles_as_dicts.append({
            'content': article[0],
            'company': article[1],
            'sentiment': article[2],
            'time': article[3].strftime('%Y-%m-%d %H:%M') + ' UTC' if article[3] else 'N/A'
        })
        
    return jsonify(articles_as_dicts)

@app.route('/healthz')
def health_check():
    """
    A simple, lightweight endpoint for the cron job to hit.
    It does nothing but return a 200 OK status and a tiny message.
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))