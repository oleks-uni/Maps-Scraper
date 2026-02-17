from playwright.sync_api import sync_playwright


def scroll_results_container(page, max_scrolls=100, scroll_delay=2000):
   
    try:
        print("Looking for results container...")
        
        # Selector for the results container based on your screenshot
        container_selector = 'div.k7jAl.miFGmb.lJ3Kh.PLbyfe'
        
        # Wait for container to be visible
        container = page.locator(container_selector).first
        container.wait_for(state="visible", timeout=10000)
        print("Found results container")
        
        # Click on the container to focus it
        container.click()
        page.wait_for_timeout(500)
        
        # Count items before scrolling
        items_before = count_result_items(page)
        print(f"Initial items count: {items_before}")
        
        no_new_items_count = 0
        
        # Scroll down multiple times to load all content
        for i in range(max_scrolls):
            print(f"Scroll {i + 1}/{max_scrolls}")
            
            # Method 1: Scroll using JavaScript on the container
            container.evaluate("el => el.scrollBy(0, 1000)")
            page.wait_for_timeout(500)
            
            # Method 2: Use keyboard to scroll (Page Down)
            page.keyboard.press("PageDown")
            page.wait_for_timeout(500)
            
            # Method 3: Use mouse wheel
            container.hover()
            page.mouse.wheel(0, 500)
            
            # Wait for new content to load
            page.wait_for_timeout(scroll_delay)
            
            # Count items after scroll
            items_after = count_result_items(page)
            print(f"Items count after scroll: {items_after}")
            
            # Check if we reached the end (no new items loaded)
            max_retry = 5
            if items_after == items_before:
                no_new_items_count += 1
                print(f"No new items loaded ({no_new_items_count}/{max_retry})")
                
                # Try scrolling to absolute bottom
                container.evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(scroll_delay)
                
                if no_new_items_count >= max_retry:
                    print("No more content to load. Stopping.")
                    break
            else:
                no_new_items_count = 0
                items_before = items_after
            
            # Check for "end of results" indicator
            try:
                end_indicator = page.locator('span.HlvSq').first
                if end_indicator.is_visible(timeout=500):
                    print("Found end of results indicator. Stopping.")
                    break
            except:
                pass
        
        # Scroll back to top to get all content
        container.evaluate("el => el.scrollTop = 0")
        page.wait_for_timeout(1000)
        
        print(f"Finished scrolling. Total items found: {count_result_items(page)}")
        return container
        
    except Exception as e:
        print(f"Error scrolling results container: {e}")
        return None


def count_result_items(page):
    """
    Counts the number of result items currently loaded in the page.
    """
    try:
        # Common selectors for Google Maps result items
        items = page.locator('div.Nv2PK').all()
        return len(items)
    except:
        return 0


def handle_cookie_consent(page):
    """
    Handles the Google cookie consent dialog if it appears.
    Looks for and clicks 'Відхилити всі' (Ukrainian) or 'Deny all' (English).
    """
    try:
        print("Checking for cookie consent dialog...")
        
        # Wait a moment for the dialog to potentially appear
        page.wait_for_timeout(2000)
        
        # Common selectors for cookie deny/reject buttons
        deny_button_selectors = [
            'button:has-text("Deny all")',
            'button:has-text("Reject all")',
            '[aria-label*="Reject" i]',
            '[aria-label*="Deny" i]',
        
        ]
        
        for selector in deny_button_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=2000):
                    button.click()
                    print("Clicked 'Deny all' button")
                    page.wait_for_timeout(1000)  # Wait for dialog to close
                    return True
            except:
                continue
        
        # Alternative: Try to find button by scrolling if dialog is long
        try:
            # Check if there's a cookie dialog/form visible
            cookie_dialog = page.locator('div[role="dialog"], form[action*="consent"], #consent-bump').first
            if cookie_dialog.is_visible(timeout=2000):
                print("Cookie dialog detected, attempting to scroll and find deny button...")
                # Scroll within the dialog
                cookie_dialog.evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(500)
                
                # Try clicking deny buttons again after scrolling
                for selector in deny_button_selectors:
                    try:
                        button = cookie_dialog.locator(selector).first
                        if button.is_visible(timeout=1000):
                            button.click()
                            print("Clicked deny button after scrolling")
                            page.wait_for_timeout(1000)
                            return True
                    except:
                        continue
        except:
            pass
        
        print("No cookie consent dialog found or already handled")
        return False
        
    except Exception as e:
        print(f"Cookie handling error (non-critical): {e}")
        return False


def search_google_maps(search_query: str,):# output_file: str = "google_maps_result.html"):
    """
    Opens Google Maps, searches for the given query, and saves the HTML page.
    
    Args:
        search_query: The search term to look up on Google Maps
        output_file: The filename to save the HTML content
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=True,
            args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            ],
            )
        
        context = browser.new_context(
            locale="en-US",
            timezone_id="America/New_York",
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            )

        
        page = context.new_page()
        
        try:
            # Navigate to Google Maps
            print("Opening Google Maps...")
            page.goto("https://www.google.com/maps?hl=en", wait_until="networkidle")
            
            # Handle cookie consent dialog if present
            handle_cookie_consent(page)
            
            # Wait for the search box to be visible
            print("Waiting for search box...")
            search_box = page.locator('input.UGojuc.fontBodyMedium.EmSKud.lpggsf').first
            search_box.wait_for(state="visible", timeout=10000)
            
            # Enter the search query
            print(f"Searching for: {search_query}")
            search_box.fill(search_query)
            
            # Press Enter to search
            search_box.press("Enter")
            
            # Wait for search results to load
            print("Waiting for results to load...")
            page.wait_for_selector('div.k7jAl.miFGmb.lJ3Kh.PLbyfe', state='visible', timeout=15000)
            page.wait_for_timeout(3000)  # Additional wait for dynamic content
            
            # Find and scroll the results container to load all data
            results_container = scroll_results_container(page)

            if results_container:
                return results_container.inner_html()
            return page.content()

        finally:
            browser.close()
            
            # Get the container's HTML
        #     if results_container:
        #         html_content = results_container.inner_html()
        #     else:
        #         # Fallback to full page content
        #         html_content = page.content()
            
        #     # Save to file
        #     with open(output_file, "w", encoding="utf-8") as f:
        #         f.write(html_content)
            
        #     print(f"HTML page saved to: {output_file}")
            
        #     return html_content
            
        # except Exception as e:
        #     print(f"Error occurred: {e}")
        #     raise
        # finally:
        #     # Close browser
        #     browser.close()


# if __name__ == "__main__":
#     # Example usage - change this to your desired search query
#     search_query = input("Enter your search query for Google Maps: ").lower()
    
#     html_result = search_google_maps(search_query)
#     print(f"\nSearch completed. HTML content length: {len(html_result)} characters")