from playwright.sync_api import sync_playwright

def click_element(page, *selectors, description="", timeout=5000):
    """Helper: Click element with multiple fallback selectors"""
    for selector in selectors:
        try:
            elem = page.locator(selector).first
            elem.click(timeout=timeout)
            print(f"✅ {description}")
            return True
        except:
            continue
    print(f"❌ {description}")
    return False

def fill_and_submit(page, selector, value, description, press_enter=False, timeout=5000):
    """Helper: Fill input and optionally press Enter"""
    try:
        elem = page.locator(selector).first
        elem.click(timeout=2000)
        elem.fill(value, timeout=timeout)
        if press_enter:
            elem.press("Enter")
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}")
        return False

def automate_easemytrip():
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_timeout(10000)
            
            # Navigate
            print("🌐 Navigating to easemytrip.com...")
            page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            print("✅ Website loaded successfully!")
            
            # Click Login or Signup
            print("🔐 Clicking on Login or Signup...")
            click_element(page, 
                         "//span[contains(text(), 'Login or Signup')]",
                         "//a/span[contains(text(), 'Login')]",
                         description="Login clicked", timeout=5000)
            page.wait_for_timeout(800)
            
            # Click My Booking (Dynamic XPath - finds any element containing text "My Booking")
            print("📖 Clicking on My Booking section...")
            click_element(page,
                         "//span[contains(., 'My Booking')]",
                         "//a[contains(., 'My Booking')]",
                         description="My Booking clicked", timeout=5000)
            page.wait_for_timeout(1500)
            
            # Enter Email (ID-based selector for stability)
            print("📧 Entering email...")
            fill_and_submit(page, "#txtEmailNew", 
                           "Abhijeet.tiwary@easemytrip.com", 
                           "Email entered", press_enter=True)
            page.wait_for_timeout(1200)
            
            # Click Continue (ID-based selector)
            print("🔐 Clicking Continue button...")
            click_element(page, "#shwotp", description="Continue clicked")
            page.wait_for_timeout(1500)
            
            # Enter Password (ID-based selector)
            print("🔑 Entering password...")
            fill_and_submit(page, "#txtEmail2", 
                           "Abhijeet9876", 
                           "Password entered")
            page.wait_for_timeout(800)
            
            # Click Login (Dynamic XPath for submit button)
            print("🔐 Clicking Login button...")
            click_element(page,
                         "//input[@type='button' and contains(@onclick, 'CheckUser')]",
                         "//input[@value='Login']",
                         description="Login clicked", timeout=5000)
            
            page.wait_for_timeout(3000)
            print("⏳ Page loading...")
            page.wait_for_timeout(3000)
            print("✅ Page loaded!")
            
            # Verify login
            current_url = page.url
            page_title = page.title()
            print(f"🌐 URL: {current_url}")
            print(f"📄 Title: {page_title}")
            
            if "mybookings.easemytrip.com" in current_url:
                print("✅ Successfully logged in!")
            
            page.wait_for_timeout(2000)
            print("📸 My Bookings page displayed on UI...")
            
            # Capture screenshot
            print("\n📷 Capturing page screenshot...")
            try:
                page.screenshot(path="mybooking_page_screenshot.png", full_page=False, timeout=30000)
                print("✅ Screenshot saved: mybooking_page_screenshot.png")
            except Exception as e:
                print(f"⚠️ Screenshot error: {e}")
            
            # Get page content
            print("\n📄 Page content displayed on UI...")
            try:
                visible_text = page.evaluate("() => document.body.innerText")
                print("=== PAGE CONTENT ===")
                print(visible_text)
                print("=== END CONTENT ===\n")
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            # Get frame info
            print("📋 Checking page frames...")
            frames = page.frames
            print(f"Total frames: {len(frames)}")
            for i, frame in enumerate(frames):
                try:
                    print(f"Frame {i}: {frame.title()} - {frame.url}")
                except:
                    pass
            
            # Get content length
            print("\n📄 Main Page Content:")
            page_content = page.content()
            print(f"Page content length: {len(page_content)} characters")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if browser:
            print("\n🔴 Closing browser...")
            try:
                browser.close()
                print("✅ Browser closed successfully!")
            except Exception as e:
                print(f"⚠️ Browser close error: {e}")
            print("✅ Script completed!")

if __name__ == "__main__":
    automate_easemytrip()
