import re
import os
import psycopg2
import hashlib

from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import Stealth

DATABASE_URL = os.getenv("DATABASE_URL")
MAX_ENTRIES = 3000
MIN_BRIEF_LENGTH = 180
MAX_BRIEF_LENGTH = 8000
KAGGLE_NOTEBOOK_ID = "kolci017/financial-news-analyzer"

def setup_database():
    """Ensures the 'briefs' table exists in the database."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id SERIAL PRIMARY KEY,
            content_hash TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            subject_company TEXT,
            sentiment TEXT,
            processed_at TIMESTAMP WITH TIME ZONE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete. Table 'briefs' is ready.")

def save_brief_to_db(briefs):
    if not briefs:
        print("Empty brief, skipping save.")
        return
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    new_briefs = 0
    for content, published_at in briefs:
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        try:
            cur.execute(
                "INSERT INTO briefs (content_hash, content, scraped_at) VALUES (%s, %s, %s) ON CONFLICT (content_hash) DO NOTHING;",
                (content_hash, content, published_at)
            )
            if cur.rowcount > 0:
                new_briefs += 1
        except Exception as e:
            print(f"An unexpected error occurred during insert: {e}")
            conn.rollback()
            
    conn.commit()
    print(f"Successfully inserted {new_briefs} entries")

    cur.execute("SELECT COUNT(id) FROM briefs;")
    total_rows = cur.fetchone()[0]
    if total_rows > MAX_ENTRIES:
        delete = total_rows - MAX_ENTRIES
        print(f"Exceeded max, removing {delete}")
        cur.execute("""
                    DELETE FROM briefs
                    WHERE id IN (
                        SELECT id FROM briefs ORDER BY scraped_at ASC LIMIT %s
                    );
                    """, (delete,))
        conn.commit()
        print(f"Successfully removed {delete}")

    cur.close()
    conn.close()

def parse_time(time_str: str) -> datetime:
    now = datetime.now(timezone.utc)
    match = re.search(r'(\d+)\s*(m|h|d)\s*ago', time_str)
    if not match:
        return now
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 'm':
        return now - timedelta(minutes=value)
    elif unit == 'h':
        return now - timedelta(hours=value)
    elif unit == 'D':
        return now - timedelta(days=value)
    return now

def scrape_and_filter_briefs():
    filtered_briefs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )
        try:
            all_items_text = [] 
            print("Applying stealth measures...")
            stealth = Stealth()
            stealth.apply_stealth_sync(context)
            page = context.new_page()

            print("Navigating to https://newsfilter.io...")
            page.goto("https://newsfilter.io", timeout=60000, wait_until="domcontentloaded")

            # Wait for the page skeleton (the "Briefs" heading)
            briefs_heading_selector = 'div:has-text("Briefs")'
            print(f"Waiting for page skeleton ('{briefs_heading_selector}')...")
            page.wait_for_selector(briefs_heading_selector, timeout=30000)
            
            # Wait for the first news item under "Briefs" to load
            first_item_selector = f'{briefs_heading_selector} + div a'
            print(f"Waiting for dynamic content ('{first_item_selector}')...")
            page.wait_for_selector(first_item_selector, timeout=30000)
            print("Dynamic content loaded.")

            sections_to_scrape = ["Briefs", "Press Releases"]
            
            print("\nScraping all news sections...")
            for section in sections_to_scrape:
                article_selector = f'div:has-text("{section}") + div a'
                list_items = page.query_selector_all(article_selector)

                for item in list_items:
                    full_text = item.text_content()
                    time = parse_time(full_text)
                    if re.match(r'\d+D',full_text):
                        # Skip items with more than 1 day old
                        continue
                    # Remove quotes
                    full_text = full_text.replace('"', "").replace("'", "")
                    # Remove parenthesis
                    full_text = re.sub(r'\([^)]*\)', '', full_text)
                    # Remove time m,h
                    full_text = re.sub(r'\d+m ', '', full_text)
                    full_text = re.sub(r'\d+h ', '', full_text)
                    # Remove ago
                    full_text = re.sub(r'ago','',full_text)
                    # Remove the symbol
                    for i in range(len(full_text)):
                        if full_text[i].islower():
                            full_text = full_text[i-1:]
                            break
                    full_text = ' '.join(full_text.split())
                    if full_text:
                        all_items_text.append((full_text,time))
            print(f"\nFiltering for items with more than {MIN_BRIEF_LENGTH} characters...")
            filtered_briefs = [
                item for item in all_items_text if len(item[0]) > MIN_BRIEF_LENGTH
            ]
            print(all_items_text)

            if not filtered_briefs:
                print("Could not find any items matching the length filter.")
                return []

            print(f"\nFound {len(filtered_briefs)} Filtered Briefs")

        except TimeoutError as e:
            print(f"\nTimeout Error: {e.message}")
            if 'page' in locals():
                page.screenshot(path="error_timeout_final.png")
            print("An error screenshot has been saved.")
        
        except Exception as e:
            print(f"An unexpected error occurred during scraping: {e}")

        finally:
            print("Closing the browser.")
            browser.close()
            
    return filtered_briefs

def trigger_kaggle_notebook():
    print(f"\n--- Triggering Kaggle Analysis on notebook: {KAGGLE_NOTEBOOK_ID} ---")
    command = f"kaggle kernels push -p ."
    exit_code = os.system(command)
    if exit_code == 0:
        print("Successfully triggered Kaggle notebook.")
    else:
        print(f"Error: Failed to trigger Kaggle notebook. Exit code: {exit_code}")


def main():
    if not DATABASE_URL:
        raise Exception("Database Url not set")
    if not KAGGLE_NOTEBOOK_ID or "your-kaggle-username" in KAGGLE_NOTEBOOK_ID:
        raise Exception("KAGGLE_NOTEBOOK_ID is not configured. Please edit the script.")
        
    try:
        print("--- Starting Scraping ---")
        setup_database()
        scraped = scrape_and_filter_briefs()
        if scraped:
            print(f"Scraped {len(scraped)} entries, saving to DB...")
            save_brief_to_db(scraped)
        else:
            print("Scraper finished but found no new entries to save.")
        print("--- Finished Scraping ---")
    finally:
        trigger_kaggle_notebook()
        print("--- Process Complete ---")


if __name__ == "__main__":
    main()