# app.py on Render - The Viewer
import os
import psycopg2
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    return render_template('index.html')

def articles():
    '''
    Returns articles as JSON for a specific date in the query
    '''

    date_str = request.args.get('date')
    target_date = None

    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"Invalid date format, use YYYY-MM-DD"}),400
    else:
        target_date = datetime.now(timezone.utc).date()
    articles = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT content, subject_company, sentiment, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                      AND CAST(scraped_at AT TIME ZONE 'UTC' AS DATE) = %s
                    ORDER BY scraped_at DESC;
                """
                cur.execute(query,(target_date))
                articles_db = cur.fetchall()
    except Exception as e:
        print(f"Fetch failed: {e}")
        return jsonify({"Failed to retrieve articles"}), 500
    articles_dict = []
    for article in articles_db:
        articles_dict.append({
            'content':article[0],
            'company':article[1],
            'sentiment':article[2],
            'time': article[3].strftime('%Y-%m-%d %H:%M') + 'UTC' if article[3] else 'N/A'
        })
    return jsonify(articles_dict)

@app.route('/healthz')
def health_check():
    """
    A simple, lightweight endpoint for the cron job to hit.
    It does nothing but return a 200 OK status and a tiny message.
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))