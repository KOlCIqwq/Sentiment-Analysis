import os
import psycopg2
import spacy
from transformers import pipeline
import torch
from flask import Flask, render_template, request, abort
import gc

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
# The secret key to verify requests from UptimeRobot
TRIGGER_SECRET = os.getenv("TRIGGER_SECRET") 

print("Loading models... This may take a while.")
NER_MODEL_PATH = "output/model-best"
SENTIMENT_MODEL_NAME = "KOlCi/distilbert-financial-sentiment"
nlp_ner = None
sentiment_pipeline = None

try:
    nlp_ner = spacy.load(NER_MODEL_PATH)
    device = -1 # Use -1 for CPU, as Render's free tier has no GPU
    sentiment_pipeline = pipeline("sentiment-analysis", model=SENTIMENT_MODEL_NAME, device=device)
    print("Models loaded successfully.")
except Exception as e:
    print(f"FATAL: Could not load models. The app will show data but cannot process new entries. Error: {e}")


@app.route('/')
def home():
    articles = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, subject_company, sentiment, scraped_at
                    FROM briefs 
                    WHERE sentiment IS NOT NULL 
                    ORDER BY scraped_at DESC 
                    LIMIT 50
                    """
                )
                articles = cur.fetchall()
    except Exception as e:
        print(f"Database query failed: {e}")
    
    return render_template('index.html', articles=articles)


@app.route('/run-analysis', methods=['POST'])
def trigger_analysis_endpoint():
    # Simple security to ensure only UptimeRobot can run this
    if request.headers.get('X-Trigger-Secret') != TRIGGER_SECRET:
        print("Forbidden: Incorrect or missing secret header.")
        abort(403)

    print("Analysis trigger received. Checking for unprocessed briefs.")
    processed_count = process_unprocessed_briefs()
    return f"Processing complete. Analyzed {processed_count} brief(s)."


def process_unprocessed_briefs():
    if not nlp_ner or not sentiment_pipeline:
        print("Models are not loaded, cannot process briefs.")
        return 0

    # Fetch up to 10 unprocessed briefs to avoid long request times
    # and stay within Render's free tier limits.
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT content_hash, content FROM briefs WHERE sentiment IS NULL LIMIT 3"
                )
                briefs_to_process = cur.fetchall()

                if not briefs_to_process:
                    print("No new briefs to process.")
                    return 0

                for content_hash, text in briefs_to_process:
                    try:
                        ner_doc = nlp_ner(text)
                        companies = ", ".join([ent.text for ent in ner_doc.ents]) or None
                        sentiment_result = sentiment_pipeline(text)
                        sentiment = sentiment_result[0]['label'].upper()

                        cur.execute(
                            """
                            UPDATE briefs
                            SET subject_company = %s, sentiment = %s, processed_at = NOW()
                            WHERE content_hash = %s
                            """,
                            (companies, sentiment, content_hash)
                        )
                        print(f"Processed: {content_hash}")
                    except Exception as e:
                        print(f"Error processing item {content_hash}: {e}")
                        conn.rollback() # Rollback the failed item but continue the loop
                
                # The 'with' block commits automatically on successful exit
    except Exception as e:
        print(f"A database error occurred during processing: {e}")
        return 0
    finally:
        # Clean up to free memory
        gc.collect()
    
    return len(briefs_to_process)


# This part is correct.
if __name__ == '__main__':
    # The port is set by Render, so this is good.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))