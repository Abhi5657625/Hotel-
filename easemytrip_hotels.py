from playwright.sync_api import sync_playwright
import time

def automate_easemytrip():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to website
        print("Navigating to easemytrip.com...")
        page.goto("https://www.easemytrip.com/", wait_until="load", timeout=60000)
        
        # Wait a moment for page to stabilize
        time.sleep(2)
        
        # Click on Hotels
        print("Clicking on Hotels...")
        try:
            page.click("text=Hotels")
            print("Hotels clicked successfully!")
        except Exception as e:
            print(f"Error clicking Hotels: {e}")
        
        # Wait to see the result
        time.sleep(5)
        print("Hotels page loaded successfully!")
        
        # Wait for Hotels page to fully load
        time.sleep(3)
        
        # Click on Search button
        print("Looking for Search button...")
        try:
            # Get all clickable elements and inspect them
            all_elements = page.query_selector_all("button, input[type='submit'], a[role='button'], [class*='btn'], [onclick]")
            
            print(f"Found {len(all_elements)} clickable elements")
            
            search_clicked = False
            
            # Try multiple search strategies
            for selector in ["text=Search", "button:has-text('Search')", "[class*='search']"]:
                try:
                    if page.query_selector(selector):
                        page.click(selector)
                        print(f"Search button clicked with selector: {selector}")
                        search_clicked = True
                        break
                except:
                    pass
            
            if not search_clicked:
                # Try clicking by XPath or data attributes
                try:
                    page.click("button[data-id='searchbtn'], button[id*='search'], button.btn-submit")
                    print("Search button clicked!")
                    search_clicked = True
                except:
                    print("Could not find Search button - inspecting page structure...")
                    # Print page HTML snippet
                    html_sample = page.content()[:2000]
                    print("Page content (first 2000 chars):")
                    print(html_sample)
        except Exception as e:
            print(f"Error: {e}")
        
        # Wait for hotel search results/listing page to load
        print("Waiting for hotel search results to load...")
        time.sleep(8)
        
        # Close popup when we navigate to listing page
        print("Attempting to close popup on listing page...")
        try:
            cross_selectors = [
                "button[aria-label='Close']",
                "button:has-text('×')",
                "[class*='close']",
                "button.close",
                "button[data-dismiss='modal']",
                "svg[class*='close']",
                "button:has-text('✕')",
                "[class*='modal-close']",
                "[class*='popup-close']",
                "div[class*='close-btn']"
            ]
            
            cross_clicked = False
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts and not cross_clicked:
                for selector in cross_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            print(f"Found close button with selector: {selector}")
                            page.click(selector)
                            print("Close button clicked successfully!")
                            cross_clicked = True
                            time.sleep(2)
                            break
                    except Exception as e:
                        continue
                
                if not cross_clicked:
                    attempt += 1
                    if attempt < max_attempts:
                        print(f"Close button not found, retrying... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(2)
            
            if not cross_clicked:
                print("Close button not found after retries, continuing...")
        
        except Exception as e:
            print(f"Error clicking close button: {e}")
        
        # Wait a moment before clicking View Rooms
        time.sleep(2)
        
        # Close "Lowest Price Guarantee" popup
        print("Attempting to close 'Lowest Price Guarantee' popup...")
        try:
            lpg_selectors = [
                ".poptrm",
                "button.poptrm",
                "[class='poptrm ng-tns-c2629078945-1']",
                "button[aria-label='Close']",
                "button:has-text('×')",
                "button:has-text('✕')",
                "div[class*='lpg'] button[class*='close']",
                "div[class*='lowest-price'] button",
                "button[class*='close-btn']",
                "[class*='guarantee'] button:has-text('×')",
                "div[role='dialog'] button:has-text('×')",
                ".modal-header button.close",
                "button[data-testid*='close']"
            ]
            
            lpg_closed = False
            
            for selector in lpg_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"Found LPG close button with selector: {selector}")
                        page.click(selector)
                        print("Lowest Price Guarantee popup closed successfully!")
                        lpg_closed = True
                        time.sleep(2)
                        break
                except Exception as e:
                    continue
            
            if not lpg_closed:
                print("Lowest Price Guarantee popup close button not found, continuing...")
        
        except Exception as e:
            print(f"Error closing Lowest Price Guarantee popup: {e}")
        
        # Wait a moment after closing popup
        time.sleep(2)
        
        # Click on View Rooms button from hotel listing
        print("Looking for 'View Rooms' button...")
        new_page = None
        try:
            page.wait_for_selector("button:has-text('View Rooms')", timeout=10000)
            
            # Use CSS selector to find the View Rooms button
            view_rooms_btn = page.query_selector("button:has-text('View Rooms')")
            
            if view_rooms_btn:
                print("Found 'View Rooms' button with selector")
                page.evaluate("el => el.scrollIntoView()", view_rooms_btn)
                time.sleep(1)
                
                # Wait for new tab and click
                with page.context.expect_page() as new_page_info:
                    view_rooms_btn.click()
                
                new_page = new_page_info.value
                print("'View Rooms' clicked successfully - new tab opened")
                page = new_page
                page.wait_for_load_state("load")
                print(f"Switched to new tab: {page.url}")
            else:
                print("'View Rooms' button not found")
        
        except Exception as e:
            print(f"Error with 'View Rooms' button: {e}")
        
        # Wait for room details to load in new tab
        if new_page is not None:
            print("Waiting for room details to load in new tab...")
            time.sleep(8)
            
            # Click on Book Now button in the new tab
            print("Looking for 'Book Now' button...")
            try:
                # Get all button/clickable elements
                all_elements = page.query_selector_all("button, a, div[role='button'], span[role='button']")
                print(f"Found {len(all_elements)} clickable elements on details page")
                
                # Look for the first element with text "Book Now"
                book_now_found = False
                for i, elem in enumerate(all_elements):
                    try:
                        elem_text = page.evaluate("el => el.textContent", elem).strip()
                        # Check exact match or partial match with "Book Now"
                        if elem_text == "Book Now" or "Book Now" in elem_text:
                            print(f"Found 'Book Now' button at index {i}")
                            page.evaluate("el => el.scrollIntoView()", elem)
                            time.sleep(1)
                            elem.click()
                            print("'Book Now' button clicked!")
                            time.sleep(4)
                            book_now_found = True
                            break
                    except:
                        pass
                
                if not book_now_found:
                    print("'Book Now' button not found")
            
            except Exception as e:
                print(f"Error clicking 'Book Now' button: {e}")
        else:
            print("No new tab was opened, skipping Book Now click")
        
         # Wait for booking page to load
        print("Waiting for booking page to fully load...")
        time.sleep(5)
        print(f"Current URL: {page.url}")
        
        # Close popup "Book above ₹5,000 to grab"
        # The popup appears on the travellers/checkout page
        if "traveller" in page.url or "checkout" in page.url:
            print("On booking/travellers page - looking for 'Dismiss' button...")
            try:
                # Wait for popup to appear
                time.sleep(5)
                
                dismiss_found = False
                
                # Strategy 1: Try pressing Escape key first
                print("  Attempting Escape key...")
                page.keyboard.press("Escape")
                time.sleep(1)
                
                # Strategy 2: Search all elements for 'Dismiss' text or 'title=Close'
                print("  Searching for Dismiss button...")
                all_clickable = page.query_selector_all("button, [role='button'], input[type='button'], a[role='button'], div[onclick], span[onclick], div[class*='button']")
                print(f"  Found {len(all_clickable)} clickable elements")
                
                for idx, elem in enumerate(all_clickable):
                    try:
                        elem_text = page.evaluate("el => (el.textContent || el.innerText || el.value || el.title || '').trim()", elem).strip()
                        elem_title = page.evaluate("el => el.getAttribute('title') || ''", elem)
                        
                        # Check for Dismiss text
                        if elem_text.lower() == "dismiss":
                            print(f"  Found Dismiss button (index {idx})")
                            page.evaluate("el => el.scrollIntoView()", elem)
                            time.sleep(0.5)
                            elem.click()
                            print("  Dismiss button clicked successfully!")
                            dismiss_found = True
                            time.sleep(2)
                            break
                        
                        # Check for title="Close"
                        if elem_title.lower() == "close":
                            print(f"  Found Close button with title='Close' (index {idx})")
                            page.evaluate("el => el.scrollIntoView()", elem)
                            time.sleep(0.5)
                            elem.click()
                            print("  Close button clicked successfully!")
                            dismiss_found = True
                            time.sleep(2)
                            break
                    except:
                        pass
                
                # Strategy 3: Check iframes for dismiss button
                if not dismiss_found:
                    iframes = page.query_selector_all("iframe")
                    for i, iframe in enumerate(iframes):
                        try:
                            frame = iframe.content_frame()
                            if frame:
                                all_btns_in_frame = frame.query_selector_all("button, [role='button'], div[onclick], input[type='button'], span[onclick]")
                                for btn in all_btns_in_frame:
                                    try:
                                        btn_text = frame.evaluate("el => (el.textContent || el.innerText || el.value || '').trim()", btn).strip()
                                        btn_title = frame.evaluate("el => el.getAttribute('title') || ''", btn)
                                        
                                        if btn_text.lower() == "dismiss":
                                            print(f"  Found Dismiss button in iframe {i}")
                                            frame.evaluate("el => el.scrollIntoView()", btn)
                                            time.sleep(0.5)
                                            btn.click()
                                            print("  Dismiss button clicked successfully!")
                                            dismiss_found = True
                                            time.sleep(2)
                                            break
                                        
                                        if btn_title.lower() == "close":
                                            print(f"  Found Close button in iframe {i} with title='Close'")
                                            frame.evaluate("el => el.scrollIntoView()", btn)
                                            time.sleep(0.5)
                                            btn.click()
                                            print("  Close button clicked successfully!")
                                            dismiss_found = True
                                            time.sleep(2)
                                            break
                                    except:
                                        pass
                                if dismiss_found:
                                    break
                        except:
                            pass
                
                # Strategy 4: Try direct attribute selectors
                if not dismiss_found:
                    attribute_selectors = [
                        "[title='Close']",
                        "[title='close']",
                        "button[title='Close']",
                        "button[title='close']",
                        "[aria-label='Close']",
                        "[aria-label='close']"
                    ]
                    
                    for selector in attribute_selectors:
                        try:
                            btn = page.query_selector(selector)
                            if btn:
                                print(f"  Found button with selector: {selector}")
                                page.evaluate("el => el.scrollIntoView()", btn)
                                time.sleep(0.5)
                                btn.click()
                                print("  Button clicked!")
                                dismiss_found = True
                                time.sleep(2)
                                break
                        except:
                            pass
                
                # Strategy 5: Try common close button selectors
                if not dismiss_found:
                    close_selectors = [
                        "button:has-text('Dismiss')",
                        "button[aria-label*='close' i]",
                        "button[class*='close']",
                        "[class*='modal'] button:last-child",
                        "[class*='popup'] button:last-child",
                        "button[onclick*='close' i]",
                        "button[onclick*='dismiss' i]"
                    ]
                    
                    for selector in close_selectors:
                        try:
                            btn = page.query_selector(selector)
                            if btn:
                                print(f"  Found button with selector: {selector}")
                                page.evaluate("el => el.scrollIntoView()", btn)
                                time.sleep(0.5)
                                btn.click()
                                print("  Button clicked!")
                                dismiss_found = True
                                time.sleep(2)
                                break
                        except:
                            pass
                
                if not dismiss_found:
                    print("  Info: Dismiss/Close button not found - popup may have auto-closed")
            
            except Exception as e:
                print(f"  Error handling popup: {e}")
        else:
            print("Not on booking page yet, skipping popup close")
        
        # Extract and display booking information
        print("\n--- Booking Information ---")
        try:
            # Try to get hotel name
            hotel_name_selectors = [
                "h1",
                "[class*='hotel-name']",
                "[class*='heading']",
                "span[class*='name']"
            ]
            
            hotel_name_found = False
            for selector in hotel_name_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        hotel_name = page.evaluate("el => el.textContent", element).strip()
                        if hotel_name and len(hotel_name) > 0:
                            print(f"Hotel: {hotel_name[:100]}")
                            hotel_name_found = True
                            break
                except:
                    continue
            
            if not hotel_name_found:
                print("Hotel name: Not found")
        
        except Exception as e:
            print(f"Error extracting hotel name: {e}")
        
        # Try to get price information
        try:
            price_selectors = [
                "[class*='price']",
                "[class*='total']",
                "span:has-text('₹')",
                "[class*='amount']"
            ]
            
            price_found = False
            for selector in price_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        for elem in elements:
                            price_text = page.evaluate("el => el.textContent", elem).strip()
                            if "₹" in price_text or "INR" in price_text:
                                print(f"Price: {price_text[:50]}")
                                price_found = True
                                break
                        if price_found:
                            break
                except:
                    continue
            
            if not price_found:
                print("Price: Not found")
        
        except Exception as e:
            print(f"Error extracting price: {e}")
        
        # Check for guest details form
        print("\n--- Checking for Guest Details Form ---")
        try:
            guest_form_selectors = [
                "[class*='guest']",
                "[class*='customer']",
                "[class*='traveller']",
                "form"
            ]
            
            guest_form_found = False
            for selector in guest_form_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"Found guest form with selector: {selector}")
                        guest_form_found = True
                        break
                except:
                    continue
            
            if not guest_form_found:
                print("Guest details form: Not visible")
        
        except Exception as e:
            print(f"Error checking guest form: {e}")
        
        # Fill guest details
        print("\n--- Filling Guest Details ---")
        try:
            # Wait for any modals or iframes to load
            time.sleep(3)
            
            # Check for iframes that might contain the form
            iframes = page.query_selector_all("iframe")
            print(f"Found {len(iframes)} iframes on page")
            
            # First, let's inspect the form structure
            print("Inspecting visible form elements...")
            
            # Look for traveller detail sections
            traveller_sections = page.query_selector_all("[class*='traveller'], [class*='guest'], [class*='pax'], [class*='customer']")
            print(f"Found {len(traveller_sections)} traveller/guest sections")
            
            # Get all visible inputs
            all_inputs = page.query_selector_all("input:not([type='hidden']):not([type='checkbox']):not([type='radio'])")
            print(f"Found {len(all_inputs)} visible text input elements")
            
            # First, try to fill the specific field by name attribute
            print("\n--- Filling First Name Field ---")
            try:
                first_name_input = page.query_selector("input[name='txtFirstName']")
                if first_name_input:
                    print("  Found input[name='txtFirstName']")
                    page.fill("input[name='txtFirstName']", "Abhi")
                    print("  Filled First Name with 'Abhi'")
                    time.sleep(0.5)
                else:
                    print("  input[name='txtFirstName'] not found")
            except Exception as e:
                print(f"  Error filling first name field: {e}")
            
            # Fill the last name field
            print("\n--- Filling Last Name Field ---")
            try:
                last_name_input = page.query_selector("input[name='txtLastName']")
                if last_name_input:
                    print("  Found input[name='txtLastName']")
                    page.fill("input[name='txtLastName']", "Test")
                    print("  Filled Last Name with 'Test'")
                    time.sleep(0.5)
                else:
                    print("  input[name='txtLastName'] not found")
            except Exception as e:
                print(f"  Error filling last name field: {e}")
            
            # Fill the email address field
            print("\n--- Filling Email Address Field ---")
            try:
                # Try to find email field by placeholder
                email_selector = "input[placeholder='Enter email address']"
                email_input = page.query_selector(email_selector)
                
                if email_input:
                    print("  Found email input with selector: input[placeholder='Enter email address']")
                    page.fill(email_selector, "abhijeet.tiwary@easemytrip.com")
                    print("  Filled Email Address with 'abhijeet.tiwary@easemytrip.com'")
                    time.sleep(0.5)
                else:
                    print("  Email field not found")
            except Exception as e:
                print(f"  Error filling email field: {e}")
            
            # Fill the mobile number field
            print("\n--- Filling Mobile Number Field ---")
            try:
                # Try to find mobile field by placeholder
                mobile_selector = "input[placeholder='Enter Mobile Number']"
                mobile_input = page.query_selector(mobile_selector)
                
                if mobile_input:
                    print("  Found mobile input with selector: input[placeholder='Enter Mobile Number']")
                    page.fill(mobile_selector, "9876543210")
                    print("  Filled Mobile Number with '9876543210'")
                    time.sleep(0.5)
                else:
                    print("  Mobile field not found")
            except Exception as e:
                print(f"  Error filling mobile field: {e}")
            
            # Try to fill inputs based on labels nearby
            for i, input_elem in enumerate(all_inputs):
                try:
                    placeholder = page.evaluate("el => el.placeholder", input_elem)
                    name_attr = page.evaluate("el => el.name", input_elem)
                    value = page.evaluate("el => el.value", input_elem)
                    is_visible = page.evaluate("el => el.offsetParent !== null", input_elem)
                    
                    if is_visible and not value:  # Only fill empty, visible inputs
                        print(f"  Input {i}: placeholder='{placeholder}', name='{name_attr}'")
                        
                        # Match by placeholder or name
                        placeholder_lower = placeholder.lower() if placeholder else ""
                        name_lower = name_attr.lower() if name_attr else ""
                        
                        if "first" in placeholder_lower or "first" in name_lower:
                            if name_attr != "txtFirstName":  # Skip if already filled above
                                page.fill(f"input:nth-of-type({i+1})", "Abhi")
                                print(f"    ✓ Filled with 'Abhi' (First Name)")
                                time.sleep(0.5)
                        elif "last" in placeholder_lower or "last" in name_lower or "surname" in placeholder_lower:
                            page.fill(f"input:nth-of-type({i+1})", "Doe")
                            print(f"    ✓ Filled with 'Doe' (Last Name)")
                            time.sleep(0.5)
                        elif "email" in placeholder_lower or "email" in name_lower:
                            page.fill(f"input:nth-of-type({i+1})", "john.doe@example.com")
                            print(f"    ✓ Filled with email")
                            time.sleep(0.5)
                        elif "phone" in placeholder_lower or "mobile" in placeholder_lower or "phone" in name_lower:
                            page.fill(f"input:nth-of-type({i+1})", "9876543210")
                            print(f"    ✓ Filled with phone number")
                            time.sleep(0.5)
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"Error filling guest details: {e}")
        
        print("\n--- Guest Details Form Completed ---")
        
        # Wait after filling form
        time.sleep(2)
        
        # Look for Continue/Proceed button and click it
        print("\n--- Looking for Continue Booking Button ---")
        try:
            continue_selectors = [
                "text=Continue Booking",
                "text=Continue",
                "text=Proceed",
                "button:has-text('Continue Booking')",
                "button:has-text('Continue')",
                "button:has-text('Proceed')",
                "button:has-text('Next')",
                "[class*='continue']",
                "[class*='proceed']"
            ]
            
            continue_found = False
            for selector in continue_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"  Found Continue button with selector: {selector}")
                        page.evaluate("el => el.scrollIntoView()", element)
                        time.sleep(0.5)
                        element.click()
                        print("  Continue Booking button clicked!")
                        continue_found = True
                        time.sleep(3)
                        break
                except:
                    continue
            
            if not continue_found:
                print("  Continue Booking button: Not found")
        
        except Exception as e:
            print(f"  Error clicking continue button: {e}")
        
        # Wait for payment page to load
        print("\n--- Waiting for Payment Page to Load ---")
        time.sleep(5)
        
        # Click on payment method: 'Choose Mobikwik, Payzapp, PhonePe or Amazon'
        print("\n--- Looking for Payment Method Button ---")
        try:
            payment_selectors = [
                "text=Choose Mobikwik, Payzapp, PhonePe or Amazon",
                "button:has-text('Choose Mobikwik')",
                "button:has-text('Mobikwik')",
                "button:has-text('Payzapp')",
                "button:has-text('PhonePe')",
                "button:has-text('Amazon')",
                "[class*='mobikwik']",
                "[class*='payzapp']",
                "[class*='phonpe']",
                "[class*='amazon']"
            ]
            
            payment_found = False
            for selector in payment_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"  Found payment method button with selector: {selector}")
                        page.evaluate("el => el.scrollIntoView()", element)
                        time.sleep(0.5)
                        element.click()
                        print("  Payment method button clicked!")
                        payment_found = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not payment_found:
                print("  Payment method button: Not found")
        
        except Exception as e:
            print(f"  Error clicking payment method button: {e}")
        
        # Wait for wallet options to load
        print("\n--- Waiting for Wallet Options to Load ---")
        time.sleep(3)
        
        # Select Bajaj Pay
        print("\n--- Looking for Bajaj Pay Option ---")
        try:
            bajaj_selectors = [
                "text=Bajaj Pay",
                "button:has-text('Bajaj Pay')",
                "label:has-text('Bajaj Pay')",
                "[class*='bajaj']",
                "input[value*='bajaj' i]"
            ]
            
            bajaj_found = False
            for selector in bajaj_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"  Found Bajaj Pay with selector: {selector}")
                        page.evaluate("el => el.scrollIntoView()", element)
                        time.sleep(0.5)
                        element.click()
                        print("  Bajaj Pay selected!")
                        bajaj_found = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not bajaj_found:
                print("  Bajaj Pay: Not found")
        
        except Exception as e:
            print(f"  Error selecting Bajaj Pay: {e}")
        
        # Wait for page to update after selecting Bajaj Pay
        print("\n--- Waiting for Make Payment Button to Appear ---")
        time.sleep(3)
        
        # Directly click on 'Make Payment' button after Bajaj Pay selection
        print("\n--- Looking for Make Payment Button ---")
        try:
            make_payment_selectors = [
                "[class='mk-pym4']",
                "[class*='mk-pym4']",
                "button[class='mk-pym4']",
                "text=Make Payment",
                "button:has-text('Make Payment')",
                "button:has-text('Pay Now')",
                "button:has-text('Submit')",
                "[class*='make-payment']",
                "[class*='makepayment']",
                "[class*='payment-btn']"
            ]
            
            make_payment_found = False
            for selector in make_payment_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        print(f"  Found Make Payment button with selector: {selector}")
                        page.evaluate("el => el.scrollIntoView()", element)
                        time.sleep(0.5)
                        element.click()
                        print("  Make Payment button clicked!")
                        make_payment_found = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not make_payment_found:
                print("  Make Payment button: Not found")
        
        except Exception as e:
            print(f"  Error clicking Make Payment button: {e}")
        
        # Display current page URL and title
        try:
            current_url = page.url
            page_title = page.title()
            print(f"\nCurrent URL: {current_url}")
            print(f"Page Title: {page_title}")
        except Exception as e:
            print(f"Error getting page info: {e}")
        
        # Take a screenshot before closing
        print("\n--- Taking Screenshot ---")
        try:
            screenshot_path = "C:\\Users\\abhijeet.tiwary\\Tid Screenshot\\booking_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        
        print("\n--- Script Execution Completed ---")
        
        # Keep browser open for viewing
        print("Browser will remain open for 15 seconds for inspection...")
        time.sleep(15)
        
        print("Closing browser...")
        browser.close()

if __name__ == "__main__":
    automate_easemytrip()
