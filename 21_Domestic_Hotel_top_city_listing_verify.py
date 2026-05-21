from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import traceback

CITY_PREFIXES = ['mum', 'del', 'kol', 'ban', 'ahm', 'hyd']
SUGGESTION_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[1]/div/div[2]/div[1]'
DIV5_INPUT_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/div[5]/input'
CITY_INPUT_ID = '#txtCity'
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

# Selectors to detect hotel listing cards on the results page
HOTEL_LISTING_SELECTORS = [
    '[class*="htlname"]',
    '[class*="htl-name"]',
    '[class*="hotel-name"]',
    '[class*="hotelName"]',
    '[class*="HotelName"]',
    '[class*="htl-list"]',
    '[class*="hotel-list"]',
    '[class*="listing-hotel"]',
    '.htlname',
    '.hotel-name',
    '[class*="htl-cont"]',
    '[class*="htlCont"]',
]

# Keywords that indicate a "no results" state on the page
NO_RESULT_KEYWORDS = [
    'no hotel found',
    'no result',
    'not found',
    '0 hotel',
    'no properties found',
    'no hotels available',
    'no hotels found',
    'hotels not available',
]

# Possible search/submit button selectors on the hotel form
SEARCH_BUTTON_SELECTORS = [
    '[class*="search-btn"]',
    '[class*="srchBtn"]',
    '[class*="SearchBtn"]',
    'button[type="submit"]',
    'input[type="submit"]',
    '[class*="btn-search"]',
]


def save_screenshot(page, name):
    """Save a screenshot for debugging on failure."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        page.screenshot(path=path)
        print(f"📸 Screenshot saved: {path}")
    except Exception:
        print("⚠️ Could not save screenshot.")


def check_hotel_listings(page, city_name):
    """
    Verify that hotel listing cards are displayed for the searched city/sector.
    Raises RuntimeError with a clear message if no listings are found.
    """
    print(f"🔎 Checking hotel listings for sector '{city_name}'...")

    # Allow up to 10 seconds for the results page / listings to render
    page.wait_for_timeout(3000)
    current_url = page.url
    print(f"📍 Current URL: {current_url}")

    # If still on homepage (not yet on hotel results page), try clicking a Search button
    is_results_page = "hotel-new/search" in current_url or "hotels.easemytrip" in current_url
    if not is_results_page:
        print("🔄 Still on homepage — attempting to click Search button...")
        search_clicked = False
        for selector in SEARCH_BUTTON_SELECTORS:
            try:
                btn = page.locator(selector).first
                if btn.is_visible():
                    btn.click()
                    search_clicked = True
                    print(f"✅ Search button clicked via selector: {selector}")
                    page.wait_for_timeout(5000)
                    break
            except Exception:
                continue
        if not search_clicked:
            print("⚠️ Could not find a Search button — proceeding with listing check on current page.")

    # Count listing cards using known selectors
    listing_count = 0
    matched_selector = None
    for selector in HOTEL_LISTING_SELECTORS:
        try:
            count = page.locator(selector).count()
            if count > 0:
                listing_count = count
                matched_selector = selector
                break
        except Exception:
            continue

    if listing_count > 0:
        print(f"✅ Hotel listings ARE coming for sector '{city_name}' — {listing_count} hotel(s) found.")
        return

    # No listing cards found — check for explicit "no results" text on the page
    try:
        page_text = page.inner_text("body").lower()
    except Exception:
        page_text = ""

    for keyword in NO_RESULT_KEYWORDS:
        if keyword in page_text:
            raise RuntimeError(
                f"❌ Hotel listings are NOT coming for sector '{city_name}' — "
                f"Page shows a 'no results' message. Please check availability for this sector."
            )

    # No cards and no explicit message — generic failure
    raise RuntimeError(
        f"❌ Hotel listings are NOT coming for sector '{city_name}' — "
        f"No hotel cards were found on the page. The results may have failed to load."
    )



def trigger_input(page, selector, value):
    """Set input value and dispatch events to trigger autocomplete."""
    try:
        page.evaluate(f"""
            var input = document.querySelector('{selector}');
            if (!input) throw new Error('Input element not found: {selector}');
            input.value = '{value}';
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """)
    except Exception as e:
        raise RuntimeError(f"❌ City input field is not working — could not type '{value}': {e}")


def load_hotel_page(page):
    """Navigate to easemytrip and open the Hotels tab."""
    try:
        page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded")
    except Exception as e:
        raise RuntimeError(f"❌ Website failed to load: {e}")

    try:
        hotel_icon = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
        hotel_icon.wait_for(state="visible", timeout=15000)
        hotel_icon.click()
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotels tab button is not working — button not visible or not clickable.")
    except Exception as e:
        raise RuntimeError(f"❌ Hotels tab button is not working: {e}")

    try:
        page.locator('xpath=/html/body/div[3]/div/div[4]/div/form/div/input[3]').wait_for(
            state="attached", timeout=10000
        )
        page.wait_for_timeout(2000)
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotel search form did not load after clicking Hotels tab.")


def search_city(page, prefix, index, total):
    print(f"\n🔄 [{index}/{total}] Searching with prefix: '{prefix}'")

    load_hotel_page(page)

    # Click the city input via JS (element is off-screen)
    try:
        element_exists = page.evaluate(f"!!document.querySelector('{CITY_INPUT_ID}')")
        if not element_exists:
            raise RuntimeError(f"❌ City input field is not working — element '{CITY_INPUT_ID}' not found on page.")
        page.evaluate(f"document.querySelector('{CITY_INPUT_ID}').click()")
        page.wait_for_timeout(1000)  # extra wait to ensure autocomplete JS is ready
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"❌ City input field is not working — could not click it: {e}")

    # Type prefix to trigger auto-suggest
    trigger_input(page, CITY_INPUT_ID, prefix)

    # Wait for suggestion to appear
    print("🔍 Reading top city from auto-suggest...")
    try:
        suggestion = page.locator(SUGGESTION_XPATH)
        suggestion.wait_for(state="visible", timeout=15000)
        top_city = suggestion.inner_text().strip()
        print(f"🏙️ Top suggested city: {top_city}")
    except PlaywrightTimeoutError:
        raise RuntimeError(
            f"❌ Auto-suggest dropdown is not working — no suggestions appeared for prefix '{prefix}'."
        )
    except Exception as e:
        raise RuntimeError(f"❌ Auto-suggest dropdown is not working: {e}")

    # Type the full city name to confirm selection
    print(f"⌨️ Typing '{top_city}' in the input field...")
    trigger_input(page, CITY_INPUT_ID, top_city)
    try:
        suggestion.wait_for(state="visible", timeout=10000)
        print(f"✅ '{top_city}' typed successfully!")
    except PlaywrightTimeoutError:
        raise RuntimeError(
            f"❌ Auto-suggest dropdown is not working — suggestions did not reappear after typing '{top_city}'."
        )

    # Click the top suggestion
    print("🖱️ Clicking on suggestion item...")
    try:
        suggestion.click()
        print("✅ Suggestion item clicked!")
    except PlaywrightTimeoutError:
        raise RuntimeError(f"❌ Suggestion button is not working — could not click suggestion for '{top_city}'.")
    except Exception as e:
        raise RuntimeError(f"❌ Suggestion button is not working: {e}")

    # Click the div[5] input (Search / date picker area)
    print("🖱️ Clicking on Search button (div[5] input)...")
    try:
        div5 = page.locator(DIV5_INPUT_XPATH)
        div5.wait_for(state="visible", timeout=10000)
        div5.click()
        print("✅ Search button clicked!")
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Search button is not working — button not visible or timed out.")
    except Exception as e:
        raise RuntimeError(f"❌ Search button is not working: {e}")

    # Wait 5 seconds as required
    print("⏳ Waiting 5 seconds...")
    page.wait_for_timeout(5000)
    print("✅ 5 seconds completed!")

    # Verify hotel listings are visible for this sector
    check_hotel_listings(page, top_city)


def automate_easemytrip():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        passed = 0
        failed = 0

        try:
            print("🌐 Navigating to easemytrip.com...")
            page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded")
            print("✅ Website loaded successfully!")

            for i, prefix in enumerate(CITY_PREFIXES, 1):
                try:
                    search_city(page, prefix, i, len(CITY_PREFIXES))
                    passed += 1
                except RuntimeError as e:
                    failed += 1
                    print(str(e))
                    save_screenshot(page, f"failure_{prefix}")
                    print(f"⚠️ Skipping prefix '{prefix}' and continuing...")
                except Exception as e:
                    failed += 1
                    print(f"❌ Unexpected error while searching '{prefix}': {e}")
                    print(traceback.format_exc())
                    save_screenshot(page, f"failure_{prefix}")
                    print(f"⚠️ Skipping prefix '{prefix}' and continuing...")

        except Exception as e:
            print(f"❌ Fatal error during automation: {e}")
            print(traceback.format_exc())
            save_screenshot(page, "fatal_error")

        finally:
            print(f"\n📊 Summary: {passed} passed, {failed} failed out of {len(CITY_PREFIXES)} cities.")
            browser.close()


if __name__ == "__main__":
    automate_easemytrip()
