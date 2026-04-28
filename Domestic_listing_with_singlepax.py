from playwright.sync_api import sync_playwright
import sys

def click_element(page, *selectors, description="", timeout=5000):
    """Click element with multiple fallback selectors and wait for visibility"""
    for selector in selectors:
        try:
            elem = page.locator(selector).first
            elem.wait_for(state="visible", timeout=timeout)
            elem.click(force=True, timeout=timeout)
            print(f"✅ {description}")
            return True
        except Exception as e:
            continue
    print(f"❌ {description} - No selector found")
    return False

def fill_input(page, selector, value, description, press_enter=False, timeout=5000):
    """Fill input field with retry logic"""
    try:
        elem = page.locator(selector).first
        elem.wait_for(state="visible", timeout=timeout)
        elem.click(force=True)
        elem.fill(value, timeout=timeout)
        if press_enter:
            elem.press("Enter")
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {str(e)[:50]}")
        return False

def wait_for_element(page, selector, state="visible", timeout=5000):
    """Wait for element to be in specific state"""
    try:
        page.locator(selector).first.wait_for(state=state, timeout=timeout)
        return True
    except:
        return False

def automate_easemytrip():
    """Automate EaseMyTrip hotel booking with LPG filter"""
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_timeout(10000)
            
            # Navigate to website
            print("🌐 Navigating to easemytrip.com...")
            page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded", timeout=30000)
            if not wait_for_element(page, "//span[contains(text(), 'hotel')]", timeout=5000):
                print("⚠️ Hotel menu not found on load")
            print("✅ Website loaded successfully!")
            
            # Click Hotel menu
            print("🏨 Clicking on Hotel menu...")
            click_element(page,
                         "//span[contains(text(), 'hotel')]",
                         "//a//span[contains(., 'Hotel')]",
                         "//li//a//span[2][contains(text(), 'hotel')]",
                         description="Hotel menu clicked", timeout=5000)
            
            # Enter city
            print("🏙️ Entering city...")
            try:
                # Try multiple selectors for city field
                city_selectors = ["#txtCity", "input[id='txtCity']", "//input[@id='txtCity']"]
                city_field = None
                for selector in city_selectors:
                    try:
                        elem = page.locator(selector).first
                        elem.wait_for(state="visible", timeout=3000)
                        city_field = elem
                        break
                    except:
                        continue
                
                if city_field:
                    city_field.clear()
                    city_field.type("New ", delay=100)
                    print("✅ City field cleared and 'New ' entered")
                else:
                    print("❌ City field not found")
            except Exception as e:
                print(f"⚠️ City entry failed: {str(e)[:50]}")
            
            # Wait for and handle autosuggest dropdown
            if wait_for_element(page, "//*[@id='autohotel6839b8f68504185ef0892327city0']", timeout=3000):
                print("✅ Autosuggest dropdown opened!")
                print("🏙️ Selecting Delhi from dropdown...")
                try:
                    page.locator("#txtCity").first.press("ArrowDown")
                    page.locator("#txtCity").first.press("Enter")
                    print("✅ Delhi selected from dropdown!")
                except Exception as e:
                    print(f"⚠️ Dropdown selection failed: {str(e)[:50]}")
            else:
                print("⚠️ Autosuggest dropdown not visible")
            
            # Select checkin date
            print("📅 Selecting checkin date...")
            try:
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[1]").first.click(force=True, timeout=2000)
                if wait_for_element(page, "//*[@id='ui-datepicker-div']", timeout=3000):
                    page.locator("xpath=//*[@id='ui-datepicker-div']/div[1]/table/tbody/tr[4]/td[6]/a").first.click(force=True, timeout=2000)
                    print("✅ Checkin date selected!")
            except Exception as e:
                print(f"⚠️ Checkin date selection failed: {str(e)[:50]}")
            
            # Select checkout date
            print("📅 Selecting checkout date...")
            try:
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[2]").first.click(force=True, timeout=2000)
                if wait_for_element(page, "//*[@id='ui-datepicker-div']", timeout=3000):
                    page.locator("xpath=//*[@id='ui-datepicker-div']/div[1]/table/tbody/tr[4]/td[6]/a").first.click(force=True, timeout=2000)
                    print("✅ Checkout date selected!")
            except Exception as e:
                print(f"⚠️ Checkout date selection failed: {str(e)[:50]}")
            
            # Select guests (with visibility handling)
            print("👥 Opening guest selection...")
            try:
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[3]").first.click(force=True, timeout=2000)
                if wait_for_element(page, "//*[@id='Adults_room_1_1']", "visible", timeout=2000):
                    page.locator("xpath=//*[@id='Adults_room_1_1']").first.click(force=True, timeout=2000)
                    print("✅ Guest selection updated!")
                else:
                    print("⚠️ Guest selection element not visible")
            except Exception as e:
                print(f"⚠️ Guest selection failed: {str(e)[:50]}")
            
            # Click Search button
            print("🔍 Clicking Search button...")
            if click_element(page, "//*[@id='btnSearch']", description="Search button clicked", timeout=5000):
                page.wait_for_load_state("networkidle", timeout=10000)
                print("✅ Search completed!")
            
    except Exception as e:
        print(f"❌ Critical error: {str(e)[:100]}")
        return False
    
    finally:
        if browser:
            print("\n🔴 Closing browser...")
            try:
                browser.close()
                print("✅ Browser closed successfully!")
            except Exception as e:
                print(f"⚠️ Browser close warning: {str(e)[:50]}")
    
    return True

if __name__ == "__main__":
    automate_easemytrip()
