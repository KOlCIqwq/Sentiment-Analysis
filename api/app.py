import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)
supabase_client = None

def get_supabase_client():
    """Creates and returns a Supabase client, reusing it if already created."""
    global supabase_client
    if supabase_client is None:

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        print(f"DEBUG: Attempting to create Supabase client.")
        print(f"DEBUG: SUPABASE_URL loaded: {'Yes' if url else 'NO - THIS IS THE PROBLEM'}")
        print(f"DEBUG: SUPABASE_SERVICE_KEY loaded: {'Yes' if key else 'NO - THIS IS THE PROBLEM'}")

        if not url or not key:
            raise ValueError("Supabase URL or Key is missing from environment variables.")
            
        supabase_client = create_client(url, key)
        print("DEBUG: Supabase client created successfully.")
    return supabase_client


@app.route('/api/debug')
def debug_check():
    """A simple endpoint to check if the API is running and can read its config."""
    print("DEBUG: /api/debug endpoint was hit.")
    try:
        # Test if we can initialize the client
        client = get_supabase_client()
        return jsonify({
            "status": "ok",
            "message": "API is running and Supabase client was initialized successfully."
        })
    except Exception as e:
        # If client creation fails, this will return a proper JSON error
        print(f"CRITICAL ERROR in debug_check: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/articles')
def api_articles():
    try:
        supabase = get_supabase_client() # Get the client
        date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        confidence_str = request.args.get('confidence', '0')
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)

        response = supabase.rpc('get_articles_by_date', {
            'target_date': str(target_date),
            'min_confidence': min_confidence
        }).execute()

        articles_as_dicts = []
        for row in response.data:
            scraped_time = datetime.fromisoformat(row['scraped_at'].replace('Z', '+00:00'))
            articles_as_dicts.append({
                'content': row['content'], 'company': row['subject_company'], 
                'sentiment': row['sentiment'], 'confidence': row['confidence'],
                'time': scraped_time.strftime('%Y-%m-%d %H:%M') + ' UTC'
            })
        return jsonify(articles_as_dicts)
    except Exception as e:
        print(f"ERROR in /api/articles: {e}")
        return jsonify({"error": "Failed to retrieve articles.", "details": str(e)}), 500


@app.route('/api/summary')
def api_summary():
    try:
        supabase = get_supabase_client() # Get the client
        date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        confidence_str = request.args.get('confidence', '0')

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_confidence = float(confidence_str)

        response = supabase.rpc('get_sentiment_summary', {
            'target_date': str(target_date),
            'min_confidence': min_confidence
        }).execute()
        
        return jsonify(response.data)
    except Exception as e:
        print(f"ERROR in /api/summary: {e}")
        return jsonify({"error": "Failed to retrieve summary.", "details": str(e)}), 500