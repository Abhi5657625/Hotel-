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
            
            # Click on Hotel menu (Dynamic XPath)
            print("🏨 Clicking on Hotel menu...")
            click_element(page,
                         "//span[contains(text(), 'hotel')]",
                         "//a//span[contains(., 'Hotel')]",
                         "//li//a//span[2][contains(text(), 'hotel')]",
                         description="Hotel menu clicked", timeout=5000)
            page.wait_for_timeout(5000)
            
            # Click on LMR checkbox (Static XPath with ID)
            print("☑️ Clicking on LMR checkbox...")
            click_element(page,
                         "//*[@id='chkLastMinute']",
                         description="LMR checkbox clicked", timeout=5000)
            page.wait_for_timeout(2000)
            
            # Enter city "New" with space to open autosuggest
            print("🏙️ Entering city...")
            try:
                # Click on city field
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/form/div").first.click(force=True, timeout=2000)
                page.wait_for_timeout(500)
                
                # Clear existing value and type "New " character by character
                page.locator("#txtCity").first.clear()
                page.locator("#txtCity").first.type("New ", delay=100)
                page.wait_for_timeout(1500)
                
                print("✅ City 'New ' entered - autosuggest should open")
                
                # Wait for autosuggest dropdown
                print("⏳ Waiting for autosuggest dropdown...")
                page.locator("xpath=//*[@id='autohotel6839b8f68504185ef0892327city0']").first.wait_for(state="visible", timeout=3000)
                print("✅ Autosuggest dropdown opened!")
                
                # Select Delhi from dropdown using keyboard navigation
                print("🏙️ Selecting Delhi from dropdown...")
                try:
                    # Press arrow down to select first option
                    page.locator("#txtCity").first.press("ArrowDown")
                    page.wait_for_timeout(300)
                    # Press Enter to select
                    page.locator("#txtCity").first.press("Enter")
                    print("✅ Delhi selected from dropdown using arrow keys!")
                except Exception as e:
                    print(f"⚠️ Could not select from dropdown: {e}")
            except Exception as e:
                print(f"⚠️ Autosuggest might not be visible: {e}")
            page.wait_for_timeout(1500)
            
            # Select checkin date - click on checkin date box to open datepicker
            print("📅 Opening datepicker for checkin date...")
            try:
                # Click on checkin date box
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[1]").first.click(force=True, timeout=2000)
                page.wait_for_timeout(1500)
                
                # Now click on the date
                page.locator("xpath=//*[@id='ui-datepicker-div']/div[1]/table/tbody/tr[4]/td[6]/a").first.click(force=True, timeout=2000)
                print("✅ Checkin date selected!")
            except Exception as e:
                print(f"⚠️ Could not select checkin date: {e}")
            page.wait_for_timeout(1500)
            
            # Select checkout date
            print("📅 Opening datepicker for checkout date...")
            try:
                # Click on checkout date box
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[2]").first.click(force=True, timeout=2000)
                page.wait_for_timeout(1500)
                
                # Click on a date (using same or different date)
                page.locator("xpath=//*[@id='ui-datepicker-div']/div[1]/table/tbody/tr[4]/td[6]/a").first.click(force=True, timeout=2000)
                print("✅ Checkout date selected!")
            except Exception as e:
                print(f"⚠️ Could not select checkout date: {e}")
            page.wait_for_timeout(1500)
            
            # Select guests - click on guest selection box
            print("👥 Opening guest selection...")
            try:
                # Click on guest selection box
                page.locator("xpath=/html/body/div[3]/div/div[4]/div/div[3]").first.click(force=True, timeout=2000)
                page.wait_for_timeout(1000)
                
                # Select 2 adults
                page.locator("xpath=//*[@id='Adults_room_1_1']").first.click(force=True, timeout=2000)
                print("✅ Guest selection opened and adults updated!")
            except Exception as e:
                print(f"⚠️ Could not select guests: {e}")
            page.wait_for_timeout(1500)
            
            # Click Search button
            print("🔍 Clicking Search button...")
            try:
                page.locator("xpath=//*[@id='btnSearch']").first.click(force=True, timeout=2000)
                print("✅ Search button clicked!")
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"⚠️ Could not click search button: {e}")
            page.wait_for_timeout(1500)
            
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

if __name__ == "__main__":
    automate_easemytrip()
