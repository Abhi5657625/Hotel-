from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CITY_NAMES = ['Dubai', 'Abu Dhabi', 'London', 'Bangkok', 'Jakarta', 'Singapore']
SUGGESTION_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[1]/div/div[2]/div[1]'
DIV5_INPUT_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/div[5]/input'
CITY_INPUT_ID = '#txtCity'
HOTEL_FORM_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/input[3]'
MAX_RETRIES = 2

def trigger_input(page, selector, value):
    """Set input value and dispatch events to trigger autocomplete."""
    page.evaluate(f"""
        var input = document.querySelector('{selector}');
        input.value = '{value}';
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
    """)

def load_hotel_page(page):
    """Navigate to easemytrip and open the Hotels tab."""
    try:
        page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded", timeout=20000)
    except PlaywrightTimeoutError:
        raise Exception("Website not responding — page load timed out. Check your internet connection.")
    except Exception as e:
        raise Exception(f"Failed to reach easemytrip.com: {e}")

    # Dismiss any popup/overlay that may intercept clicks
    try:
        popup = page.locator('#offr_pp')
        popup.wait_for(state="visible", timeout=5000)
        page.evaluate("document.getElementById('offr_pp').style.display='none'")
    except Exception:
        pass  # No popup, continue

    try:
        hotel_icon = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
        hotel_icon.wait_for(state="visible", timeout=15000)
        hotel_icon.click()
    except PlaywrightTimeoutError:
        raise Exception("Hotels tab not found or not responding — site layout may have changed.")

    try:
        page.locator(HOTEL_FORM_XPATH).wait_for(state="attached", timeout=10000)
    except PlaywrightTimeoutError:
        raise Exception("Hotel search form did not load — page may not be responding.")

def reset_or_reload(page):
    """Reset city input if hotel form is still attached, otherwise do a full reload."""
    try:
        form = page.locator(HOTEL_FORM_XPATH)
        form.wait_for(state="attached", timeout=3000)
        page.evaluate(f"document.querySelector('{CITY_INPUT_ID}').value = ''")
    except Exception:
        load_hotel_page(page)

def search_city(page, city, index, total):
    print(f"\n🔄 [{index}/{total}] Searching for: '{city}'")

    # Step 1: Click the city input
    try:
        page.evaluate(f"document.querySelector('{CITY_INPUT_ID}').click()")
    except Exception as e:
        raise Exception(f"City input field not found or not responding: {e}")

    # Step 2: Type city name to trigger auto-suggest
    try:
        trigger_input(page, CITY_INPUT_ID, city)
    except Exception as e:
        raise Exception(f"Failed to type city name '{city}' into input field: {e}")

    # Step 3: Wait for suggestion to appear
    print("🔍 Reading top city from auto-suggest...")
    try:
        suggestion = page.locator(SUGGESTION_XPATH)
        suggestion.wait_for(state="visible", timeout=15000)
        top_city = suggestion.inner_text().strip()
        print(f"🏙️ Top suggested city: {top_city}")
    except PlaywrightTimeoutError:
        raise Exception(f"Auto-suggest dropdown did not appear for '{city}' — not responding or city not found.")

    # Step 4: Click the top suggestion
    print("🖱️ Clicking on suggestion item...")
    try:
        suggestion.click()
        print("✅ Suggestion item clicked!")
    except PlaywrightTimeoutError:
        raise Exception(f"Suggestion item for '{city}' is not clickable — not responding.")
    except Exception as e:
        raise Exception(f"Could not click suggestion for '{city}': {e}")

    # Step 5: Click the div[5] input
    print("🖱️ Clicking on input at div[5]...")
    try:
        div5 = page.locator(DIV5_INPUT_XPATH)
        div5.wait_for(state="visible", timeout=10000)
        div5.click()
        print("✅ div[5] input clicked!")
    except PlaywrightTimeoutError:
        raise Exception("Search/confirm button (div[5]) not found or not responding.")
    except Exception as e:
        raise Exception(f"Could not click div[5] input: {e}")

    page.wait_for_timeout(3000)
    print(f"✅ '{city}' search completed!")

def automate_easemytrip():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        results = {}

        # Initial page load
        try:
            print("🌐 Navigating to easemytrip.com...")
            load_hotel_page(page)
            print("✅ Website loaded successfully!")
        except Exception as e:
            print(f"\n❌ FATAL: Could not load website — {e}")
            browser.close()
            return

        # Search each city with retry
        for i, city in enumerate(CITY_NAMES, 1):
            success = False
            last_error = None

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if i > 1 or attempt > 1:
                        reset_or_reload(page)
                    search_city(page, city, i, len(CITY_NAMES))
                    results[city] = '✅ Pass'
                    success = True
                    break
                except Exception as e:
                    last_error = str(e)
                    if attempt < MAX_RETRIES:
                        print(f"  ⚠️ Attempt {attempt} failed: {last_error}")
                        print(f"  🔁 Retrying '{city}'...")
                        try:
                            load_hotel_page(page)
                        except Exception:
                            pass

            if not success:
                results[city] = f'❌ Not Working — {last_error}'
                print(f"  ❌ '{city}' failed after {MAX_RETRIES} attempt(s): {last_error}")
                try:
                    load_hotel_page(page)
                except Exception:
                    pass

        # Final summary report
        passed = [c for c, r in results.items() if r.startswith('✅')]
        failed  = [c for c, r in results.items() if r.startswith('❌')]

        print("\n" + "=" * 60)
        print("📊  FINAL RESULTS SUMMARY")
        print("=" * 60)
        for city, result in results.items():
            print(f"  {result} — {city}")
        print("-" * 60)
        print(f"  Total: {len(CITY_NAMES)}  |  Passed: {len(passed)}  |  Failed: {len(failed)}")
        if failed:
            print(f"\n  ⚠️  Cities not working / not responding:")
            for city in failed:
                print(f"      • {city}  →  {results[city]}")
        else:
            print("\n  🎉 All cities searched successfully!")
        print("=" * 60)

        browser.close()

if __name__ == "__main__":
    automate_easemytrip()
