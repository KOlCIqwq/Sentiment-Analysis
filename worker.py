import os
import time
import psycopg2
import psycorg2.extesions
import spacy
from transformers import pipeline
import torch

print("Loading models... This might take a moment.")
NER_MODEL_PATH = "output/model-best"
SENTIMENT_MODEL_NAME = "KOlCi/distilbert-financial-sentiment"
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    nlp_ner = spacy.load(NER_MODEL_PATH)
    print(f"NER model loaded")

    device = 0 if torch.cuda.is_available() else -1  # Use GPU if available, otherwise CPU
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=SENTIMENT_MODEL_NAME,
        device=device
    )
    print(f"Sentiment model loaded")
except Exception as e:
    print(f"Could not load model: {e}")
    exit()

def analyze_and_update_brief(content):
    """Fetches, analyzes, and updates a single brief in the database."""
    print(f"Analyzing brief: {str[:50]}...")  # Print first 50 characters for context
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    try:
        cur.execute("SELECT content FROM briefs WHERE content_hash = %s;", (content,))
        result = cur.fetchone()
        if not result:
            print("Brief not found in database.")
            return
        text = result[0]

        ner_doc = nlp_ner(text)
        companies = ''.join([ent.text for ent in ner_doc.ents]) or None
        
        sentiment_result = sentiment_pipeline(text)
        sentiment = sentiment_result[0]['label'].upper()

        cur.execute("""
            UPDATE briefs
            SET subject_company = %s, sentiment = %s, processed_at = NOW()
            WHERE content_hash = %s
            """,
            (companies,sentiment,content)
        )
        conn.commit()
        print(f"Brief updated with sentiment: {sentiment} and companies: {companies}")
    except Exception as e:
        print(f"Error processing brief: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def listen_for_new_briefs():
    """Listens for new briefs and processes them."""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("LISTEN new_brief_channel;")
    print("Listening for new briefs...")
    while True:
        if psycopg2.select.select([conn], [], [], 60) == ([], [], []):
            print("Listener timeout, still alive...")
            continue
    
        conn.poll()
        while conn.notifies:
            notification = conn.notifies.pop(0)
            print(f"Received notification: {notification.payload}")
            analyze_and_update_brief(notification.payload)
        cur.close()
        conn.close()

if __name__ == "__main__":
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set!")

    listen_for_new_briefs()