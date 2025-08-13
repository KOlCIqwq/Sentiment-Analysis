# app.py on Render - The Viewer
import os
import psycopg2
from flask import Flask, render_template, jsonify 

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    return render_template('index.html')

def get_latest_articles():
    """Helper function to fetch the 50 most recent processed articles."""
    articles = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # --- REVERTED QUERY ---
                # This is the original, simple query that just gets the
                # 50 most recent entries that have been processed.
                cur.execute(
                    """
                    SELECT content, subject_company, sentiment, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                    ORDER BY scraped_at DESC
                    LIMIT 50;
                    """
                )
                articles = cur.fetchall()
    except Exception as e:
        print(f"Database query failed: {e}")
    return articles


@app.route('/api/articles')
def api_articles():
    """Returns the latest articles as JSON."""
    db_articles = get_latest_articles() 
    
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