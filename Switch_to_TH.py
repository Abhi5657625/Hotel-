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
            
            # Click on Indian flag
            print("🇮🇳 Clicking on Indian flag...")
            indian_flag = page.locator('//*[@id="spnCC"]')
            indian_flag.click()
            print("✅ Indian flag clicked!")
            
            # Wait for dropdown to open
            page.wait_for_timeout(1000)
            
            # Click on UAE flag
            print("🇦🇪 Clicking on UAE flag...")
            uae_flag = page.locator('//*[@id="divCCaption"]')
            uae_flag.click()
            print("✅ UAE flag clicked!")
            
            # Wait for dropdown options to load
            page.wait_for_timeout(1000)
            
            # Click on Thailand portal
            print("🌐 Clicking on Thailand portal...")
            th_portal = page.locator('//*[@id="lanCountry"]/div/div/div[2]/div[4]')
            th_portal.click()
            print("✅ Thailand portal clicked!")
            
            # Wait for result to load and display for 5 seconds
            print("⏳ Waiting 5 seconds for results to display...")
            page.wait_for_timeout(5000)
            print("✅ 5 seconds completed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
