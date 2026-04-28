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
            
            # Click on search field
            print("🔍 Clicking on search field...")
            search_field = page.locator('xpath=/html/body/div[3]/div/div[4]/div/form/div')
            search_field.click()
            print("✅ Search field clicked!")
            
            # Wait for dropdown to load
            page.wait_for_timeout(1000)
            
            # Select popular location
            print("📍 Selecting popular location...")
            location = page.locator('//*[@id="divTopCity"]/div/div[3]/a[2]')
            location.click(force=True)
            print("✅ Location selected!")
            
            # Click on element
            print("🔘 Clicking on element...")
            element = page.locator('xpath=/html/body/div[3]/div/div[4]/div/div[1]')
            element.click()
            print("✅ Element clicked!")
            
            # Get current date and add 2 days for checkout
            today = datetime.now()
            checkin = today.strftime("%d")
            checkout = (today + timedelta(days=2)).strftime("%d")
            
            # Click on check-in date
            print("📅 Clicking on check-in date...")
            checkin_xpath = f'//*[@id="ui-datepicker-div"]/div[1]//a[text()="{checkin}"]'
            checkin_date = page.locator(checkin_xpath).first
            checkin_date.click()
            print(f"✅ Check-in date {checkin} selected!")
            
            # Click on checkout box
            print("📦 Clicking on checkout box...")
            checkout_box = page.locator('xpath=/html/body/div[3]/div/div[4]/div/div[2]')
            checkout_box.click()
            print("✅ Checkout box clicked!")
            
            # Wait for datepicker to appear
            page.wait_for_timeout(500)
            
            # Click on checkout date
            print("📅 Clicking on checkout date...")
            checkout_xpath = f'//*[@id="ui-datepicker-div"]/div[1]//a[text()="{checkout}"]'
            checkout_date = page.locator(checkout_xpath).first
            checkout_date.click()
            print(f"✅ Checkout date {checkout} selected!")
            
            # Click on guest selection box
            print("👥 Clicking on guest selection box...")
            guest_box = page.locator('xpath=/html/body/div[3]/div/div[4]/div/div[3]')
            guest_box.click()
            print("✅ Guest selection box clicked!")
            
            # Wait for guest panel to appear
            page.wait_for_timeout(500)
            
            # Click on pax panel
            print("🔽 Clicking on pax panel...")
            pax_panel = page.locator('//*[@id="divPaxPanel"]/p/i')
            pax_panel.click()
            print("✅ Pax panel clicked!")
            
            # Click to add child
            print("➕ Adding child guest...")
            add_child = page.locator('//*[@id="Children_room_1_1_plus"]')
            add_child.click()
            print("✅ Child added!")
            
            # Click on child selection
            print("👶 Clicking on child selection...")
            child_select = page.locator('//*[@id="Children_room_1_1"]')
            child_select.click()
            print("✅ Child selection clicked!")
            
            # Click on child age selection
            print("🎂 Clicking on child age selection...")
            child_age = page.locator('//*[@id="Child_Age_1_1"]')
            child_age.click()
            print("✅ Child age selection clicked!")
            
            # Select age 10
            print("📋 Selecting age 10...")
            page.wait_for_timeout(500)
            child_age.select_option("10")
            print("✅ Age 10 selected!")
            
            # Click search button
            print("🔍 Clicking search button...")
            search_button = page.locator('//*[@id="btnSearch"]')
            search_button.click()
            print("✅ Search button clicked!")
            
            # Wait for results to load
            page.wait_for_timeout(3000)
            print("✅ Search results loaded!")
            
            # Click LPG filter
            print("🔍 Applying LPG filter...")
            lpg_filter = page.locator('//*[@id="filterPanel"]/filter-panel/div/div[1]/div[2]/div/div/label[1]/div[1]/div[1]')
            lpg_filter.click()
            print("✅ LPG filter applied!")
            
            # Wait for filtered results
            page.wait_for_timeout(2000)
            
            # Click on hotel result
            print("🏨 Clicking on hotel result...")
            
            # Set up listener for new page
            with page.context.expect_page() as new_page_info:
                hotel_result = page.locator('xpath=/html/body/app-root/div/hotel-srp/div[3]/div[2]/result-tupple/div[4]/div/div[1]/div[2]/div[1]/div[1]/div[1]/div/a')
                hotel_result.click()
            
            # Get the new page
            new_page = new_page_info.value
            print("✅ Hotel result clicked!")
            print("📄 New tab opened for room selection")
            
            # Wait for new page with domcontentloaded
            new_page.wait_for_load_state("domcontentloaded")
            print("✅ Hotel details page loaded!")
            
            # Wait a bit more for content to render
            new_page.wait_for_timeout(2000)
            print("✅ Ready to select room!")
            
            # Click on room to select
            print("🛏️ Selecting room...")
            room_button = new_page.locator('xpath=/html/body/app-root/div/hotel-details/div[1]/div/image-slider/div/div[2]/div[2]/div[3]/a[2]')
            room_button.click()
            print("✅ Room selected!")
            
            # Wait for next page to load
            new_page.wait_for_timeout(2000)
            
            # Close cashback popup
            print("❌ Closing cashback popup...")
            cashback_popup = new_page.locator('xpath=/html/body/app-root/div/app-hotel-traveller/div[3]/div/div[1]')
            cashback_popup.click()
            print("✅ Cashback popup closed!")
            
            # Select adult title
            print("👤 Selecting adult title...")
            title_select = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[2]/div[2]/span/select')
            title_select.select_option("Mr.")
            print("✅ Adult title 'Mr.' selected!")
            
            # Enter first name
            print("📝 Entering first name...")
            first_name = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[2]/div[3]/input')
            first_name.fill("Abhijeet")
            print("✅ First name 'Abhijeet' entered!")
            
            # Enter last name
            print("📝 Entering last name...")
            last_name = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[2]/div[4]/input')
            last_name.fill("Test")
            print("✅ Last name 'Test' entered!")
            
            # Select child title
            print("👶 Selecting child title...")
            child_title = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[3]/div/div[2]/span/select')
            child_title.select_option("Master")
            print("✅ Child title 'Master' selected!")
            
            # Enter child first name
            print("📝 Entering child first name...")
            child_first_name = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[3]/div/div[3]/input')
            child_first_name.fill("abc")
            print("✅ Child first name 'abc' entered!")
            
            # Enter child last name
            print("📝 Entering child last name...")
            child_last_name = new_page.locator('//*[@id="guestDetails"]/div[3]/div[2]/div[3]/div/div[4]/input')
            child_last_name.fill("abc")
            print("✅ Child last name 'abc' entered!")
            
            # Enter email
            print("📧 Entering email...")
            email = new_page.locator('//*[@id="guestDetails"]/div[3]/div[3]/div[1]/input')
            email.fill("abhijeet.tiwary@easemytrip.com")
            print("✅ Email 'abhijeet.tiwary@easemytrip.com' entered!")
            
            # Enter mobile number
            print("📱 Entering mobile number...")
            mobile = new_page.locator('//*[@id="guestDetails"]/div[3]/div[3]/div[2]/input[1]')
            mobile.fill("9625314180")
            print("✅ Mobile number '9625314180' entered!")
            
            # Click continue button
            print("🔘 Clicking continue button...")
            continue_button = new_page.locator('//*[@id="divHotelDetails"]/form/div/div[7]/button')
            continue_button.click()
            print("✅ Continue button clicked!")
            
            # Wait for payment page to load
            new_page.wait_for_timeout(3000)
            
            # Click on card payment option
            print("💳 Clicking on card payment option...")
            card_option = new_page.locator('//*[@id="payment_form"]/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[1]/div[2]/div/div[2]/div[2]')
            card_option.click()
            print("✅ Card payment option selected!")
            
            # Wait for card form to load
            new_page.wait_for_timeout(1000)
            
            # Enter card number
            print("🔢 Entering card number...")
            card_input = new_page.locator('//*[@id="card-input"]')
            card_input.fill("5405290007803007")
            print("✅ Card number '5405290007803007' entered!")
            
            # Enter card validity
            print("📅 Entering card validity...")
            validity = new_page.locator('input[type="tel"].CCMMYY')
            validity.fill("08 31")
            print("✅ Card validity '08 31' entered!")
            
            # Enter card CVV
            print("🔐 Entering card CVV...")
            cvv = new_page.locator('//*[@id="CCCVV"]')
            cvv.fill("515")
            print("✅ Card CVV '515' entered!")
            
            # Enter cardholder name
            print("👤 Entering cardholder name...")
            cardholder = new_page.locator('//*[@id="CCN"]')
            cardholder.fill("Nishant pitti")
            print("✅ Cardholder name 'Nishant pitti' entered!")
            
            # Click make payment button
            print("💳 Clicking make payment button...")
            pay_button = new_page.locator('//*[@id="card"]/div[7]/div[2]')
            pay_button.click()
            print("✅ Make payment button clicked!")
            
            # Wait for ICICI bank page to load in frame
            new_page.wait_for_timeout(3000)
            print("🏦 ICICI bank page loaded in frame")
            
            # Get all frames on the page
            frames = new_page.frames
            print(f"📊 Found {len(frames)} frame(s)")
            
            # Wait for frame to be ready
            new_page.wait_for_timeout(2000)
            
            # Cancel payment in the frame
            print("❌ Cancelling payment...")
            cancel_button = new_page.locator('//*[@id="otpPin"]/div[3]/button[2]')
            cancel_button.click()
            print("✅ Payment cancelled!")
            
            # Wait for TID to be generated
            new_page.wait_for_timeout(2000)
            print("⏳ TID generating...")
            
            # Get the failed TID element
            print("🎫 Capturing failed TID...")
            tid_element = new_page.locator('//*[@id="divTicket"]/div[2]/div[1]/div[2]')
            tid_text = tid_element.text_content()
            print(f"❌ Failed TID: {tid_text}")
            
            # Take screenshot of the TID element
            print("📸 Taking screenshot of failed TID...")
            new_page.screenshot(path="failed_tid_screenshot.png")
            print("✅ Screenshot saved as 'failed_tid_screenshot.png'")
            print("✅ Automation completed successfully!")
            print("🔒 Closing browser...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    automate_easemytrip()
