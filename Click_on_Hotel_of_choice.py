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
            
            # Click on hotel of choice
            print("🏨 Clicking on hotel of choice...")
            hotel_choice = page.locator('//*[@id="htlchoice"]/div/div[2]/div[1]/div/div[8]/div/a/div/div[1]')
            hotel_choice.click()
            print("✅ Hotel of choice clicked!")
            
            # Wait for 5 seconds
            print("⏳ Waiting 5 seconds...")
            page.wait_for_timeout(5000)
            print("✅ 5 seconds completed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
