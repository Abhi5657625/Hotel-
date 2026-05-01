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
            
            # Wait for page to load after closing popup
            print("⏳ Waiting for page to load...")
            page.wait_for_timeout(3000)
            
            # Click on search field to trigger autosuggest
            print("🔍 Clicking on search field...")
            search_field = page.locator('xpath=/html/body/div[3]/div/div[4]/div/form/div')
            search_field.click()
            print("✅ Search field clicked!")
            
            # Wait for autosuggest to open and populate
            print("⏳ Waiting for autosuggest to load...")
            page.wait_for_timeout(5000)
            
            # Try to click on popular domestic location
            print("🏠 Clicking on popular domestic location...")
            try:
                domestic_location = page.locator('xpath=//*[@id="divTopCity"]/div/div[3]/a[2]')
                domestic_location.click()
                print("✅ Popular domestic location clicked!")
            except Exception as e:
                print(f"⚠️ Could not click with specific XPath: {e}")
                print("🔍 Trying alternative selector...")
                # Try using CSS selector for any link with text
                all_links = page.locator('a')
                print(f"Found {all_links.count()} links on the page")
            
            # Wait for 5 seconds after domestic location selection
            print("⏳ Waiting 5 seconds...")
            page.wait_for_timeout(5000)
            print("✅ 5 seconds completed!")
            
            # Close browser
            print("❌ Closing browser...")
            browser.close()
            print("✅ Browser closed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
