from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

def automate_easemytrip():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to website
            print("🌐 Navigating to easemytrip.com...")
            page.goto("https://www.easemytrip.com/")
            
            print("✅ Website loaded successfully!")
            
            # Click on hotel icon
            print("🏨 Clicking on hotel icon...")
            hotel_icon = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
            hotel_icon.click()
            print("✅ Hotel icon clicked!")
            
            # Wait for popup to appear
            page.wait_for_timeout(1000)
            
            # Close summerfest popup
            print("❌ Closing summerfest popup...")
            close_popup = page.locator('//*[@id="offr_pp"]/div/a[1]')
            close_popup.click()
            print("✅ Summerfest popup closed!")
            
            # Wait for offer page to load
            page.wait_for_timeout(2000)
            
            # Click on read more link
            print("🎯 Clicking on read more...")
            read_more = page.locator('xpath=/html/body/div[15]/div[3]/a')
            read_more.click()
            print("✅ Read more clicked!")
            
            # Wait for 2 seconds
            page.wait_for_timeout(2000)
            
            # Click on near-me
            print("🎯 Clicking on near-me...")
            near_me = page.locator('xpath=/html/body/div[15]/div[2]/a')
            near_me.click()
            print("✅ Near-me clicked!")
            
            # Wait until results are displayed using fluent wait
            print("⏳ Waiting for results to load...")
            page.wait_for_load_state('networkidle')
            print("✅ Results displayed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
