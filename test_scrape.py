from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import Stealth

def scrape_and_filter_briefs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )

        MIN_BRIEF_LENGTH = 180

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
            all_items_text = []
            sections_to_scrape = ["Briefs", "Press Releases"]
            
            print("\nScraping all news sections...")
            for section in sections_to_scrape:
                article_selector = f'div:has-text("{section}") + div a'
                list_items = page.query_selector_all(article_selector)
                for item in list_items:
                    full_text = item.text_content()
                    if full_text:
                        all_items_text.append(' '.join(full_text.split()))

            # Apply the length filter to get only the briefs
            print(f"\nFiltering for items with more than {MIN_BRIEF_LENGTH} characters...")
            filtered_briefs = [
                text for text in all_items_text if len(text) > MIN_BRIEF_LENGTH
            ]

            if not filtered_briefs:
                print("Could not find any items matching the length filter.")
                return

            print(f"\n--- Found {len(filtered_briefs)} Filtered Briefs ---")
            for text in filtered_briefs:
                print(f"- {text}")

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

if __name__ == "__main__":
    scrape_and_filter_briefs()