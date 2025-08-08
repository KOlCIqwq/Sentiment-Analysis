import re
import os
import psycopg2

from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import Stealth

DATABASE_URL = os.getenv("DATABASE_URL")
MAX_ENTRIES = 300
MIN_BRIEF_LENGTH = 180

def setup_database():
    """Ensures the 'briefs' table exists in the database."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id SERIAL PRIMARY KEY,
            content TEXT UNIQUE NOT NULL,
            scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database setup complete. Table 'briefs' is ready.")

def save_brief_to_db(brief):
    if not brief:
        print("Empty brief, skipping save.")
        return
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    new_briefs = 0
    for b in brief:
        try:
            cur.execute("Insert value (%s)", b)
            new_briefs += 1
        except psycopg2.IntegrityError:
            # Already exist in database
            pass
    conn.commit()
    print(f"Successfully inserted {new_briefs}")

    cur.execute("SELECT COUNT(id) FROM briefs;") # Select all
    total_rows = cur.fetchone()[0]
    if total_rows > MAX_ENTRIES:
        delete = total_rows - MAX_ENTRIES
        print(f"Exceeded max, removing {delete}")
        cur.execute("""
                    DELETE FROM briefs
                    WHERE id IN (
                        SELECT id FROM briefs ORDER BY scraped_at ASC LIMIT %s
                    );
                    """, (delete))
        conn.commit()
        print(f"Successfully removed {delete}")

    cur.close()
    conn.close()

def scrape_and_filter_briefs():
    all_items_text = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )

        try:
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

            # Scrape all sections to prepare for filtering
            sections_to_scrape = ["Briefs", "Press Releases"]
            
            print("\nScraping all news sections...")
            for section in sections_to_scrape:
                article_selector = f'div:has-text("{section}") + div a'
                list_items = page.query_selector_all(article_selector)
                for item in list_items:
                    full_text = item.text_content()
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
                        all_items_text.append(full_text)

            # Apply the length filter to get only the briefs
            print(f"\nFiltering for items with more than {MIN_BRIEF_LENGTH} characters...")
            filtered_briefs = [
                text for text in all_items_text if len(text) > MIN_BRIEF_LENGTH
            ]

            if not filtered_briefs:
                print("Could not find any items matching the length filter.")
                return

            print(f"\nFound {len(filtered_briefs)} Filtered Briefs")
            """ for text in filtered_briefs:
                print(f"- {text}") """

        except TimeoutError as e:
            print(f"\nTimeout Error: {e.message}")
            if 'page' in locals():
                page.screenshot(path="error_timeout_final.png")
            print("An error screenshot has been saved.")
        
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        finally:
            print("Closing the browser.")
            browser.close()
        return filtered_briefs

def main():
    if not DATABASE_URL:
        raise Exception("Database Url not set")
    print("Start Scraping")
    setup_database()
    scraped = scrape_and_filter_briefs()
    print(scraped)
    save_brief_to_db(scraped)
    print("Finished Scraping")

if __name__ == "__main__":
    main()