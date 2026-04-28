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
            
            # Click on sign-in/signup button
            print("🔐 Clicking on sign-in/signup button...")
            signin_button = page.locator('//*[@id="divSignInPnl"]/a/span')
            signin_button.click()
            print("✅ Sign-in/signup button clicked!")
            
            # Wait for popup to appear
            page.wait_for_timeout(1000)
            
            # Click on login button
            print("📝 Clicking on login button...")
            login_button = page.locator('//*[@id="shwlogn"]/span[2]')
            login_button.click()
            print("✅ Login button clicked!")
            
            # Wait for login form to load
            page.wait_for_timeout(1000)
            
            # Click on email field
            print("📧 Clicking on email field...")
            email_field = page.locator('//*[@id="lgnBox"]/div[1]/div[2]/div/label')
            email_field.click()
            print("✅ Email field clicked!")
            
            # Insert email
            print("📧 Entering email...")
            email_field.fill("Abhijeet.tiwary@easemytrip.com")
            page.keyboard.press("Space")
            page.keyboard.press("Enter")
            print("✅ Email entered and submitted!")
            
            # Wait for OTP/continue screen
            page.wait_for_timeout(1500)
            
            # Click continue button
            print("🔘 Clicking continue button...")
            continue_button = page.locator('//*[@id="shwotp"]')
            continue_button.click()
            print("✅ Continue button clicked!")
            
            # Wait for password field to appear
            page.wait_for_timeout(1000)
            
            # Click on password field
            print("🔐 Clicking on password field...")
            password_field = page.locator('//*[@id="emailgnBox"]/div/div[2]/div/label')
            password_field.click()
            print("✅ Password field clicked!")
            
            # Insert password
            print("🔐 Entering password...")
            password_field.fill("Abhijeet9876")
            print("✅ Password entered!")
            
            # Wait for login button to be ready
            page.wait_for_timeout(500)
            
            # Click on login button
            print("🔘 Clicking on login button...")
            final_login_button = page.locator('//*[@id="emailgnBox"]/div/div[5]/input')
            final_login_button.click()
            print("✅ Login button clicked!")
            
            # Wait for page to load after login
            page.wait_for_timeout(2000)
            
            # Close popup
            print("❌ Closing popup...")
            close_popup = page.locator('//*[@id="ProfileBox"]/div[1]/div[2]/div[3]')
            close_popup.click()
            print("✅ Popup closed!")
            
            # Wait for 5 seconds before closing browser
            print("⏳ Waiting for 5 seconds...")
            page.wait_for_timeout(5000)
            print("✅ 5 seconds wait completed!")
            
            print("✅ Login automation completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
