import os
import psycopg2
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/articles')
def api_articles():
    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    confidence_str = request.args.get('confidence', '0')
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date or confidence format."}), 400

    articles_db = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT content, subject_company, sentiment, confidence, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                    AND CAST(scraped_at AT TIME ZONE 'UTC' AS DATE) = %s
                    AND confidence >= %s
                    ORDER BY scraped_at DESC;
                """
                cur.execute(query, (target_date, min_confidence))
                articles_db = cur.fetchall()
    except Exception as e:
        print(f"Database articles query failed: {e}")
        return jsonify({"error": "Failed to retrieve articles."}), 500

    articles_as_dicts = []
    for row in articles_db:
        articles_as_dicts.append({
            'content': row[0], 'company': row[1], 'sentiment': row[2],
            'confidence': row[3],
            'time': row[4].strftime('%Y-%m-%d %H:%M') + ' UTC' if row[4] else 'N/A'
        })
    return jsonify(articles_as_dicts)

@app.route('/api/summary')
def api_summary():
    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    confidence_str = request.args.get('confidence', '0')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date or confidence format."}), 400

    summary = {}
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Daily Summary (for the selected day)
                daily_query = """
                    SELECT sentiment, COUNT(*) FROM briefs
                    WHERE sentiment IS NOT NULL
                    AND CAST(scraped_at AT TIME ZONE 'UTC' AS DATE) = %s
                    AND confidence >= %s
                    GROUP BY sentiment;
                """
                cur.execute(daily_query, (target_date, min_confidence))
                daily_results = dict(cur.fetchall())
                summary['daily'] = {
                    'positive': daily_results.get('POSITIVE', 0),
                    'negative': daily_results.get('NEGATIVE', 0),
                    'neutral': daily_results.get('NEUTRAL', 0)
                }

                # Monthly Summary (for the month of the selected day)
                monthly_query = """
                    SELECT sentiment, COUNT(*) FROM briefs
                    WHERE sentiment IN ('POSITIVE', 'NEGATIVE')
                    AND scraped_at >= DATE_TRUNC('month', %s::date)
                    AND scraped_at < DATE_TRUNC('month', %s::date) + INTERVAL '1 month'
                    AND confidence >= %s
                    GROUP BY sentiment;
                """
                cur.execute(monthly_query, (target_date, target_date, min_confidence))
                monthly_results = dict(cur.fetchall())
                summary['monthly'] = {
                    'positive': monthly_results.get('POSITIVE', 0),
                    'negative': monthly_results.get('NEGATIVE', 0)
                }
    except Exception as e:
        print(f"Database summary query failed: {e}")
        return jsonify({"error": "Failed to retrieve summary."}), 500
        
    return jsonify(summary)

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))