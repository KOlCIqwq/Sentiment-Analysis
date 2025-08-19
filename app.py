# app.py on Render - The Viewer
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
def articles():
    '''
    Returns articles as JSON for a specific date in the query
    '''

    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    target_date = None
    confidence_filter = request.args.get('confidence', 'all')

    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"Invalid date format, use YYYY-MM-DD"}),400
    else:
        target_date = datetime.now(timezone.utc).date()

    articles_db = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT content, subject_company, sentiment, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                    AND CAST(scraped_at AT TIME ZONE 'UTC' AS DATE) = %s
                """
                if confidence_filter == 'high':
                    query += " AND confidence >= 0.85"
                query += " ORDER BY scraped_at DESC;"

                cur.execute(query,tuple([target_date]))
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
            'confidence':article[3],
            'time': article[4].strftime('%Y-%m-%d %H:%M') + 'UTC' if article[4] else 'N/A'
        })
    return jsonify(articles_dict)

@app.route('/api/summary')
def api_summary():
    '''
    Return summary statistics for the top bar
    '''
    confidence_filter = request.args.get('confidence', 'all')
    confidence_sql = "AND confidence >= 0.85" if confidence_filter == 'high' else ""

    summary = {}
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                daily_req = f"""
                    SELECT COUNT(*) FROM briefs
                    WHERE sentiment IS NOT NULL
                    AND CAST(scraped_at AT TIME ZONE 'UTC' AS DATE) = CAST(NOW() AT TIME ZONE 'UTC' AS DATE)
                    {confidence_sql};
                """
                cur.execute(daily_req)
                summary['daily_count'] = cur.fetchone()[0]
                # Get monthly counts
                monthly_req = f"""
                    SELECT sentiment, COUNT(*) FROM briefs
                    WHERE sentiment IS NOT NULL
                    AND scraped_at >= DATE_TRUNC('month', NOW() AT TIME ZONE 'UTC')
                    {confidence_sql}
                    GROUP BY sentiment;
                """
                cur.execute(monthly_req)
                monthly_out = dict(cur.fetchall())
                summary['month_pos'] = monthly_out.get('POSITIVE')
                summary['month_neg'] = monthly_out.get('NEGATIVE')
                summary['month_neu'] = monthly_out.get('NEUTRAL')
    except Exception as e:
        print(f"Database summary query failed: {e}")
        return jsonify({"error": "Failed to retrieve summary."}), 500
    return jsonify(summary)

@app.route('/healthz')
def health_check():
    """
    A simple, lightweight endpoint for the cron job to hit.
    It does nothing but return a 200 OK status and a tiny message.
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))