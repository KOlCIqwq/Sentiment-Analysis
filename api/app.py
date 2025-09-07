import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@app.route('/api/articles')
def api_articles():
    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    confidence_str = request.args.get('confidence', '0')
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date or confidence format."}), 400

    try:
        # Use the Supabase client to build the query
        response = supabase.table('briefs').select(
            "content, subject_company, sentiment, confidence, scraped_at"
        ).not_.is_( # WHERE sentiment IS NOT NULL
            'sentiment', 'null'
        ).gte( # AND confidence >= %s
            'confidence', min_confidence
        ).eq( # AND CAST(scraped_at AS DATE) = %s
            'scraped_at::date', str(target_date)
        ).order( # ORDER BY scraped_at DESC
            'scraped_at', desc=True
        ).execute()

        articles_as_dicts = []
        for row in response.data:
            scraped_time = datetime.fromisoformat(row['scraped_at'])
            articles_as_dicts.append({
                'content': row['content'], 'company': row['subject_company'], 
                'sentiment': row['sentiment'], 'confidence': row['confidence'],
                'time': scraped_time.strftime('%Y-%m-%d %H:%M') + ' UTC'
            })
        return jsonify(articles_as_dicts)

    except Exception as e:
        print(f"API articles query failed: {e}")
        return jsonify({"error": "Failed to retrieve articles."}), 500

@app.route('/api/summary')
def api_summary():
    date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    confidence_str = request.args.get('confidence', '0')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date or confidence format."}), 400

    try:
        # Call the database function we created
        response = supabase.rpc('get_sentiment_summary', {
            'target_date': str(target_date),
            'min_confidence': min_confidence
        }).execute()
        
        # The function returns a single JSON object with the structure we need
        summary = response.data
        return jsonify(summary)
    except Exception as e:
        print(f"Database summary query failed: {e}")
        return jsonify({"error": "Failed to retrieve summary."}), 500

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))