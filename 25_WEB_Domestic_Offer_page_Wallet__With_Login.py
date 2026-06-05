import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import traceback
import random

# Login credentials
LOGIN_EMAIL    = "abhijeet.tiwary@easemytrip.com"
LOGIN_PASSWORD = "Abhijeet9876"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


def save_screenshot(page, name):
    """Save a screenshot for debugging on failure."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        page.screenshot(path=path)
        print(f"📸 Screenshot saved: {path}")
    except Exception:
        print("⚠️ Could not save screenshot.")


def perform_login(page):
    """Login: hover → Customer Login → email → continue → password → login."""
    print("🖱️ Hovering over login element...")
    try:
        page.locator('a._btnclick').first.hover()
        print("✅ Hovered via class selector")
        page.wait_for_timeout(200)
    except Exception as e:
        print(f"⚠️ Hover failed: {e}")

    print("🔐 Clicking 'Customer Login'...")
    page.evaluate("""
        () => {
            var spans = Array.from(document.querySelectorAll('span'));
            var el = spans.find(function(s) { return s.innerText.trim() === 'Customer Login'; });
            if (el) el.click();
        }
    """)
    print("✅ Clicked 'Customer Login' via JS")

    try:
        page.locator('#txtEmail').wait_for(state="visible", timeout=10000)
    except Exception:
        page.wait_for_timeout(1500)

    print(f"📧 Entering email: {LOGIN_EMAIL}")
    try:
        email_input = page.locator('#txtEmail').first
        email_input.click(force=True)
        email_input.fill(LOGIN_EMAIL)
        print("✅ Email entered via #txtEmail")
        page.keyboard.press("Enter")
    except Exception as e:
        print(f"⚠️ #txtEmail failed: {e}")

    page.wait_for_timeout(300)

    print("▶️ Clicking Continue...")
    for name in ["Continue", "Next", "Proceed"]:
        try:
            btn = page.get_by_role("button", name=name).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                print(f"✅ Continue clicked via button '{name}'")
                break
        except Exception:
            continue

    print("⏳ Waiting for password field...")
    try:
        page.locator('#txtEmail2').wait_for(state="visible", timeout=10000)
        print("✅ Password field is now visible")
    except Exception:
        page.wait_for_timeout(2000)

    print("🔑 Entering password...")
    try:
        pwd_input = page.locator('#txtEmail2').first
        pwd_input.scroll_into_view_if_needed()
        pwd_input.click(force=True)
        pwd_input.fill(LOGIN_PASSWORD)
        print("✅ Password entered via #txtEmail2")
    except Exception as e:
        print(f"⚠️ #txtEmail2 failed: {e}")

    page.wait_for_timeout(200)

    print("🚀 Clicking Login button...")
    for name in ["Login", "Sign In", "Log In", "Submit"]:
        try:
            btn = page.get_by_role("button", name=name).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                print(f"✅ Login clicked via button '{name}'")
                break
        except Exception:
            continue

    try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(300)
    print(f"✅ Login complete. Current URL: {page.url}")


def click_offer_section(page):
    """
    Click the offer banner on the Hotel home page after login.
    Uses the XPath: /html/body/section[1]/div[2]/div/div[1]/div[4]/a/div[1]/img
    The offer opens in a new tab — captures and returns the new tab page.
    """
    print("\n🎯 Clicking on Offer section (hotel home page)...")

    # Scroll down a bit to ensure offer banners are in view
    page.evaluate("window.scrollBy(0, 300)")
    page.wait_for_timeout(200)

    # ── Priority 1: Exact XPath (offer image, div[4] banner) ──────────
    for xpath, label in [
        ('xpath=/html/body/section[1]/div[2]/div/div[1]/div[4]/a/div[1]/img', 'img XPath div[4]'),
        ('xpath=/html/body/section[1]/div[2]/div/div[1]/div[4]/a',            'anchor XPath div[4]'),
        ('xpath=/html/body/section[1]/div[2]/div/div[1]/div[5]/a/div[1]/img', 'img XPath div[5]'),
        ('xpath=/html/body/section[1]/div[2]/div/div[1]/div[5]/a',            'anchor XPath div[5]'),
    ]:
        try:
            el = page.locator(xpath).first
            el.wait_for(state="attached", timeout=6000)
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            print(f"🖱️ Found offer element via: {label}")
            with page.context.expect_page(timeout=12000) as new_page_info:
                el.click(force=True)
            new_tab = new_page_info.value
            new_tab.wait_for_load_state("domcontentloaded")
            print(f"✅ New tab opened. URL: {new_tab.url}")
            return new_tab
        except Exception as e:
            print(f"⚠️ {label} — {e}")
            continue

    # ── Priority 2: CSS — offer/deal banners on hotel page ────────────
    for selector in [
        '[class*="offer"] a[target="_blank"]',
        '[class*="Offer"] a[target="_blank"]',
        '[class*="deal"] a[target="_blank"]',
        '[class*="banner"] a[target="_blank"]',
        '[class*="promo"] a[target="_blank"]',
        'a[target="_blank"][href*="offer"]',
        'a[target="_blank"][href*="deal"]',
    ]:
        try:
            el = page.locator(selector).first
            if el.count() > 0 and el.is_visible():
                print(f"🖱️ Found offer element via CSS: {selector}")
                with page.context.expect_page(timeout=10000) as new_page_info:
                    el.click()
                new_tab = new_page_info.value
                new_tab.wait_for_load_state("domcontentloaded")
                print(f"✅ New tab opened. URL: {new_tab.url}")
                return new_tab
        except Exception:
            continue

    # ── Priority 3: JS — first visible target=_blank offer link ───────
    try:
        with page.context.expect_page(timeout=10000) as new_page_info:
            page.evaluate("""
                () => {
                    var keywords = ['offer', 'deal', 'promo', 'discount', 'coupon'];
                    var links = Array.from(document.querySelectorAll('a[target="_blank"]'));
                    for (var a of links) {
                        var href = (a.href || '').toLowerCase();
                        if (keywords.some(function(k) { return href.includes(k); })
                                && a.offsetParent !== null) {
                            a.click(); return;
                        }
                    }
                    var anyBlank = links.find(function(a) { return a.offsetParent !== null; });
                    if (anyBlank) anyBlank.click();
                }
            """)
        new_tab = new_page_info.value
        new_tab.wait_for_load_state("domcontentloaded")
        print(f"✅ New tab opened via JS fallback. URL: {new_tab.url}")
        return new_tab
    except Exception as e:
        raise RuntimeError(f"❌ Could not find or click the Offer section: {e}")


def automate_easemytrip():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print("🌐 Starting easemytrip.com automation...")

            # ── Step 1: Launch easemytrip.com ────────────────────────────
            print("\n📌 Step 1: Launching easemytrip.com...")
            page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded")
            print(f"✅ Loaded: {page.url}")

            # ── Step 2: Click Hotels tab ──────────────────────────────────
            print("\n📌 Step 2: Clicking Hotels tab...")
            try:
                hotel_tab = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
                hotel_tab.wait_for(state="visible", timeout=15000)
                hotel_tab.click()
                print("✅ Hotels tab clicked")
            except Exception as e:
                raise RuntimeError(f"❌ Hotels tab not clickable: {e}")

            # ── Step 3: Login ─────────────────────────────────────────────
            print("\n📌 Step 3: Performing login...")
            perform_login(page)

            # ── Step 4: Click Offer section on hotel home page → new tab ──
            print("\n📌 Step 4: Clicking Offer section on hotel home page...")

            # After login, page lands on https://www.easemytrip.com/hotels/
            try:
                page.wait_for_load_state("networkidle", timeout=6000)
            except Exception:
                pass
            page.wait_for_timeout(500)
            print(f"📍 Current URL (hotel home page): {page.url}")

            new_tab = click_offer_section(page)

            # ── Step 5: Switched to new tab ───────────────────────────────
            print(f"\n📌 Step 5: Switched to new tab successfully!")
            print(f"   🌐 New tab URL: {new_tab.url}")
            print(f"   📄 Page title : {new_tab.title()}")

            # ── Step 6: Click element on new tab ──────────────────────────
            print(f"\n📌 Step 6: Clicking element on new tab...")
            STEP6_XPATH = 'xpath=/html/body/div[1]/div[3]/div/div[3]/div/form/div/div[3]/span[1]'
            try:
                el = new_tab.locator(STEP6_XPATH).first
                el.wait_for(state="attached", timeout=15000)
                el.scroll_into_view_if_needed()
                el.click(force=True)
                print(f"✅ Element clicked via XPath: {STEP6_XPATH}")
                print(f"📄 Current URL: {new_tab.url}")
            except Exception as e:
                raise RuntimeError(f"❌ Could not click element on new tab: {e}")

            # ── Step 7: Click city input & type 'delhi' ───────────────────
            print(f"\n📌 Step 7: Clicking city input and typing 'delhi'...")
            STEP7_XPATH = 'xpath=/html/body/div[1]/div[3]/div/div[3]/div/form/div/input[3]'
            try:
                el = new_tab.locator(STEP7_XPATH).first
                el.wait_for(state="attached", timeout=10000)
                el.scroll_into_view_if_needed()
                el.click(force=True)
                el.fill("delhi")
                print(f"✅ Clicked input and typed 'delhi' via XPath: {STEP7_XPATH}")
            except Exception as e:
                raise RuntimeError(f"❌ Could not click/type in city input on new tab: {e}")

            # ── Step 8: Select first auto-suggest location ────────────────
            print(f"\n📌 Step 8: Selecting first auto-suggest location...")
            try:
                # Common auto-suggest list selectors — try each until one appears
                suggestion_selectors = [
                    'xpath=/html/body/div[1]/div[3]/div/div[3]/div/form/div/div[3]/ul/li[1]',
                    'xpath=/html/body/div[1]/div[3]/div/div[3]/div/form/div/ul/li[1]',
                    '[class*="autoSuggest"] li:first-child',
                    '[class*="auto-suggest"] li:first-child',
                    '[class*="suggestion"] li:first-child',
                    '[class*="dropdown"] li:first-child',
                    '[class*="autosuggest"] li:first-child',
                    'ul[class*="suggest"] li:first-child',
                    'ul[class*="Suggest"] li:first-child',
                    'ul.ui-autocomplete li:first-child',
                    '[role="listbox"] [role="option"]:first-child',
                    '[role="option"]:first-child',
                ]

                first_item = None
                for sel in suggestion_selectors:
                    try:
                        el = new_tab.locator(sel).first
                        el.wait_for(state="visible", timeout=5000)
                        if el.count() > 0 and el.is_visible():
                            first_item = el
                            print(f"🔍 Auto-suggest found via: {sel}")
                            break
                    except Exception:
                        continue

                if first_item is None:
                    raise RuntimeError("No auto-suggest dropdown appeared after typing 'delhi'.")

                suggestion_text = first_item.inner_text().strip()
                print(f"🏙️ First suggestion: {suggestion_text}")
                first_item.click()
                print(f"✅ First auto-suggest location selected: '{suggestion_text}'")

            except Exception as e:
                raise RuntimeError(f"❌ Auto-suggest selection failed: {e}")

            # ── Step 9: Select check-in date (2 days from today) ─────────
            print(f"\n📌 Step 9: Selecting check-in date (2 days from today)...")
            from datetime import datetime, timedelta
            checkin_date = datetime.today() + timedelta(days=2)
            checkin_day  = str(checkin_date.day)
            checkin_str  = checkin_date.strftime("%d/%m/%Y")
            print(f"📅 Check-in date: {checkin_str}")
            try:
                # txtCheckInDate is hidden — trigger via JS to open datepicker
                new_tab.evaluate("document.querySelector('#txtCheckInDate').click()")
                new_tab.wait_for_timeout(400)
                print("📆 Datepicker triggered via JS click on #txtCheckInDate")
                new_tab.locator('#ui-datepicker-div').wait_for(state="visible", timeout=6000)
                print("📆 Datepicker panel is visible")
                day_link = new_tab.locator(
                    f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{checkin_day}")'
                ).first
                day_link.wait_for(state="attached", timeout=5000)
                day_link.click(force=True)
                new_tab.wait_for_timeout(200)
                print(f"✅ Check-in day {checkin_day} selected ({checkin_str})")

            except Exception as e:
                raise RuntimeError(f"❌ Check-in date selection failed: {e}")

            # ── Step 10: Select check-out date (2 days after check-in) ──────
            print(f"\n📌 Step 10: Selecting check-out date (2 days after check-in)...")
            checkout_date = checkin_date + timedelta(days=2)
            checkout_day  = str(checkout_date.day)
            checkout_str  = checkout_date.strftime("%d/%m/%Y")
            print(f"📅 Check-out date: {checkout_str}")
            try:
                # txtCheckOutDate is also hidden — trigger via JS
                new_tab.evaluate("document.querySelector('#txtCheckOutDate').click()")
                new_tab.wait_for_timeout(400)
                print("📆 Datepicker triggered via JS click on #txtCheckOutDate")
                new_tab.locator('#ui-datepicker-div').wait_for(state="visible", timeout=6000)
                print("📆 Datepicker panel is visible")
                day_link = new_tab.locator(
                    f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{checkout_day}")'
                ).first
                day_link.wait_for(state="attached", timeout=5000)
                day_link.click(force=True)
                new_tab.wait_for_timeout(200)
                print(f"✅ Check-out day {checkout_day} selected ({checkout_str})")

            except Exception as e:
                raise RuntimeError(f"❌ Check-out date selection failed: {e}")

            # ── Step 11: Configure 2 rooms (2 adults + 1 child each) ────────
            print(f"\n📌 Step 11: Configuring rooms — 2 rooms, 2 adults + 1 child each...")
            try:
                new_tab.keyboard.press("Escape")
                new_tab.wait_for_timeout(200)

                # Open Rooms & Guests panel
                new_tab.evaluate("""
                    () => {
                        var p = document.getElementById('divPaxPanel');
                        if (p) p.click();
                        var panel = document.getElementById('divHotelPaxContent');
                        if (panel) { panel.style.display = 'block'; panel.style.visibility = 'visible'; }
                    }
                """)
                new_tab.wait_for_timeout(400)
                print("🛏️ Rooms & Guests panel opened")

                # Room 1: +1 adult (1→2), +1 child, set age 5
                new_tab.evaluate("""
                    () => {
                        document.getElementById('Adults_room_1_1_plus').click();
                        document.getElementById('Children_room_1_1_plus').click();
                        var s = document.getElementById('Child_Age_1_1');
                        if (s) { s.value = '5'; s.dispatchEvent(new Event('change', {bubbles:true})); }
                    }
                """)
                new_tab.wait_for_timeout(300)
                print("   ✅ Room 1: 2 adults, 1 child (age 5)")

                # Add Room 2
                new_tab.evaluate("() => { document.getElementById('addhotelRoom').click(); }")
                new_tab.wait_for_timeout(800)
                print("   ✅ Room 2 added")

                # Room 2: +1 adult (1→2), +1 child, set age 10
                new_tab.evaluate("""
                    () => {
                        document.getElementById('Adults_room_2_2_plus').click();
                        document.getElementById('Children_room_2_2_plus').click();
                        var s = document.getElementById('Child_Age_2_1');
                        if (s) { s.value = '10'; s.dispatchEvent(new Event('change', {bubbles:true})); }
                    }
                """)
                new_tab.wait_for_timeout(300)
                print("   ✅ Room 2: 2 adults, 1 child (age 10)")

                # Click Done
                new_tab.evaluate("() => { document.getElementById('exithotelroom').click(); }")
                new_tab.wait_for_timeout(300)
                print("✅ Rooms configured: 2 rooms × (2 adults + 1 child)")

            except Exception as e:
                raise RuntimeError(f"❌ Room configuration failed: {e}")

            # ── Step 12: Click Search button ─────────────────────────────────
            print(f"\n📌 Step 12: Clicking Search button...")
            try:
                new_tab.evaluate("() => { document.getElementById('btnSearch').click(); }")
                print("✅ Search button clicked via JS (#btnSearch)")
                new_tab.wait_for_load_state("domcontentloaded", timeout=15000)
                new_tab.wait_for_timeout(2000)
                print(f"✅ Search results page loaded: {new_tab.url}")
            except Exception as e:
                raise RuntimeError(f"❌ Search button click failed: {e}")

            # ── Step 13: Click a RANDOM 'View Rooms' on hotel results ──────────
            print(f"\n📌 Step 13: Clicking a RANDOM 'View Rooms' button...")
            vr_tab = None
            try:
                # Collect all hotel details links and pick one at random
                all_details_links = new_tab.locator('a[href*="hotel-new/details"]')
                all_details_links.first.wait_for(state="attached", timeout=10000)
                total_links = all_details_links.count()
                chosen_idx = random.randint(0, max(0, total_links - 1))
                print(f"🎲 Randomly selected hotel index {chosen_idx} out of {total_links} available")

                details_link = all_details_links.nth(chosen_idx)
                details_href = details_link.get_attribute("href", timeout=5000)
                print(f"🖱️ Found details link: {details_href[:80]}...")

                try:
                    with new_tab.context.expect_page(timeout=6000) as vr_page_info:
                        details_link.click(force=True)
                    vr_tab = vr_page_info.value
                    vr_tab.wait_for_load_state("domcontentloaded", timeout=15000)
                    print(f"✅ View Rooms opened new tab: {vr_tab.url}")
                except Exception:
                    # No new tab — navigate directly via href in same tab
                    if not details_href.startswith("http"):
                        details_href = "https://www.easemytrip.com" + details_href
                    new_tab.goto(details_href)
                    new_tab.wait_for_load_state("domcontentloaded", timeout=15000)
                    vr_tab = new_tab
                    print(f"✅ View Rooms navigated (same tab): {vr_tab.url}")

            except Exception as e:
                raise RuntimeError(f"❌ View Rooms click failed: {e}")

            # ── Step 14: Click "Book Now" on hotel details page ──────────────
            print(f"\n📌 Step 14: Clicking 'Book Now' on hotel details page...")
            try:
                details_page = vr_tab
                details_page.wait_for_load_state("domcontentloaded", timeout=15000)
                details_page.wait_for_timeout(1000)
                print(f"   🌐 Details page URL: {details_page.url}")

                for sel in [
                    'a.fill-btn',
                    'a:has-text("Book Now")',
                    'button:has-text("Book Now")',
                    '[class*="fill-btn"]',
                ]:
                    try:
                        el = details_page.locator(sel).first
                        el.wait_for(state="attached", timeout=5000)
                        el.scroll_into_view_if_needed()
                        el.click(force=True)
                        details_page.wait_for_load_state("domcontentloaded", timeout=15000)
                        print(f"✅ Book Now clicked via: {sel}")
                        print(f"   🌐 After click URL: {details_page.url}")
                        break
                    except Exception:
                        continue
                else:
                    raise RuntimeError("'Book Now' button not found on details page")

            except Exception as e:
                raise RuntimeError(f"❌ Book Now click failed: {e}")

            # ── Step 15: Click "Let's Go!" popup on travellers page ──────────
            print(f"\n📌 Step 15: Clicking 'Let's Go!' popup button...")
            try:
                travellers_page = details_page
                travellers_page.wait_for_timeout(1000)
                print(f"   🌐 Travellers page URL: {travellers_page.url}")

                for sel in [
                    "a.lets-go",
                    '[class*="lets-go"]',
                    'a:has-text("Let\'s Go!")',
                    'a:has-text("Lets Go")',
                    'button:has-text("Let\'s Go")',
                    '[class*="letsgo"]',
                ]:
                    try:
                        el = travellers_page.locator(sel).first
                        el.wait_for(state="visible", timeout=6000)
                        if el.is_visible():
                            el.scroll_into_view_if_needed()
                            el.click(force=True)
                            travellers_page.wait_for_timeout(800)
                            print(f"✅ 'Let's Go!' clicked via: {sel}")
                            print(f"   🌐 Page after click: {travellers_page.url}")
                            break
                    except Exception:
                        continue
                else:
                    info = travellers_page.evaluate("""
                        () => {
                            var els = Array.from(document.querySelectorAll('a,button'));
                            return els.filter(function(e){
                                var rect = e.getBoundingClientRect();
                                return rect.width > 0 && (e.innerText||'').trim().length > 0;
                            }).slice(0,30).map(function(e,i){
                                return i+': '+e.tagName+' text="'+(e.innerText||'').trim().substring(0,40)+'" class="'+(e.className||'').substring(0,50)+'"';
                            }).join('\\n');
                        }
                    """)
                    print("📋 Visible buttons on travellers page:")
                    for line in info.split('\n'):
                        print(f"   {line}")
                    raise RuntimeError("'Let's Go!' button not found — see debug above")

            except Exception as e:
                raise RuntimeError(f"❌ Let's Go click failed: {e}")

            # ── Step 16: Enter traveller details ──────────────────────────────
            print(f"\n📌 Step 16: Entering traveller details...")
            try:
                travellers_page.wait_for_timeout(800)

                fn_loc = travellers_page.locator('input[name="txtFirstName"]')
                ln_loc = travellers_page.locator('input[name="txtLastName"]')

                def fill_nth(locator, n, value, label):
                    el = locator.nth(n)
                    el.wait_for(state="attached", timeout=5000)
                    el.click(force=True)
                    el.fill(value)
                    print(f"   ✅ {label} → '{value}' (nth={n})")

                # Adult 1 (nth 0): Anshul Sharma
                fill_nth(fn_loc, 0, "Anshul",  "Adult 1 First Name")
                fill_nth(ln_loc, 0, "Sharma",  "Adult 1 Last Name")

                # Adult 2 (nth 1): Manish Kumar
                fill_nth(fn_loc, 1, "Manish",  "Adult 2 First Name")
                fill_nth(ln_loc, 1, "Kumar",   "Adult 2 Last Name")

                # Child 1 (nth 2 if exists, else debug): Santosh Kumar
                child_count = fn_loc.count()
                print(f"   ℹ️  Total txtFirstName fields found: {child_count}")
                if child_count > 2:
                    fill_nth(fn_loc, 2, "Santosh", "Child 1 First Name")
                    fill_nth(ln_loc, 2, "Kumar",   "Child 1 Last Name")
                else:
                    # Children may use different field names — debug
                    info = travellers_page.evaluate("""
                        () => Array.from(document.querySelectorAll('input[type="text"],input[type=""]')).map((e,i) =>
                            i+': id="'+(e.id||'')+'" name="'+(e.name||'')+'" placeholder="'+(e.placeholder||'')+'"'
                        ).join('\\n')
                    """)
                    print("📋 Text inputs (child field lookup):")
                    for line in info.split('\n'):
                        print(f"   {line}")
                    print("   ⚠️  Child name field not at nth=2; check debug above")

                # Child 2 (nth 3): Shivam Kumar
                if child_count > 3:
                    fill_nth(fn_loc, 3, "Shivam", "Child 2 First Name")
                    fill_nth(ln_loc, 3, "Kumar",  "Child 2 Last Name")
                else:
                    print(f"   ⚠️  Child 2 field not found (only {child_count} name fields)")

                # Phone number
                phone_selectors = [
                    'input[placeholder="Enter Mobile Number"]',
                    'input[name*="mobile"]', 'input[name*="phone"]',
                    'input[id*="mobile"]', 'input[id*="phone"]',
                    'input[placeholder*="Mobile"]', 'input[placeholder*="Phone"]',
                ]
                phone_filled = False
                for sel in phone_selectors:
                    try:
                        el = travellers_page.locator(sel).first
                        el.wait_for(state="attached", timeout=3000)
                        el.click(force=True)
                        el.fill("8707040722")
                        print(f"   ✅ Phone Number → '8707040722' via: {sel}")
                        phone_filled = True
                        break
                    except Exception:
                        continue
                if not phone_filled:
                    print("   ⚠️  Phone field not found")

            except Exception as e:
                raise RuntimeError(f"❌ Traveller details entry failed: {e}")

            # ── Step 17: Click Continue button ────────────────────────────────
            print(f"\n📌 Step 17: Clicking 'Continue' button...")
            try:
                for sel in [
                    'button:has-text("Continue")',
                    'a:has-text("Continue")',
                    'input[value="Continue"]',
                    '[class*="continue"]',
                    '[id*="continue"]',
                    'button[type="submit"]',
                ]:
                    try:
                        el = travellers_page.locator(sel).first
                        el.wait_for(state="visible", timeout=5000)
                        if el.is_visible():
                            el.scroll_into_view_if_needed()
                            el.click(force=True)
                            travellers_page.wait_for_load_state("domcontentloaded", timeout=15000)
                            print(f"✅ Continue clicked via: {sel}")
                            print(f"   🌐 Page after Continue: {travellers_page.url}")
                            break
                    except Exception:
                        continue
                else:
                    info = travellers_page.evaluate("""
                        () => Array.from(document.querySelectorAll('a,button,input[type="submit"]'))
                            .filter(e => { var r=e.getBoundingClientRect(); return r.width>0 && (e.innerText||e.value||'').trim().length>0; })
                            .slice(0,30).map((e,i) =>
                                i+': '+e.tagName+' text="'+(e.innerText||e.value||'').trim().substring(0,40)+'" class="'+(e.className||'').substring(0,50)+'"'
                            ).join('\\n')
                    """)
                    print("📋 Visible buttons (Continue lookup):")
                    for line in info.split('\n'):
                        print(f"   {line}")
                    raise RuntimeError("'Continue' button not found — see debug above")

            except Exception as e:
                raise RuntimeError(f"❌ Continue click failed: {e}")

            # ── Step 18: Click element on checkout page ────────────────────────
            print(f"\n📌 Step 18: Clicking element on checkout page...")
            try:
                checkout_page = travellers_page
                # Wait for navigation to checkout URL
                try:
                    checkout_page.wait_for_url("**/checkout/checkout**", timeout=20000)
                except Exception:
                    pass
                checkout_page.wait_for_load_state("load", timeout=20000)
                checkout_page.wait_for_timeout(5000)
                print(f"   🌐 Checkout page URL: {checkout_page.url}")

                wallet_section_xpath = "/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[6]"
                label_xpath = "/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[6]/div[1]/div[2]/div[5]/label"

                # ── Step 18a: Click Wallet section to expand it ────────────
                print(f"   💳 Step 18a: Clicking Wallet section to expand...")
                wallet_opened = False

                # Try via class selector for wallet section header
                try:
                    el_sec = checkout_page.locator(".pymtsbtxt.ng-binding").filter(
                        has_text="Mobikwik"
                    ).first
                    el_sec.wait_for(state="attached", timeout=8000)
                    el_sec.scroll_into_view_if_needed()
                    el_sec.click(force=True)
                    wallet_opened = True
                    print(f"   ✅ Wallet section clicked via .pymtsbtxt.ng-binding selector")
                except Exception:
                    pass

                if not wallet_opened:
                    # Try XPath via JS
                    try:
                        result = checkout_page.evaluate("""
                            (xp) => {
                                var n = document.evaluate(xp, document, null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                if (n) { n.click(); return true; }
                                return false;
                            }
                        """, wallet_section_xpath)
                        if result:
                            wallet_opened = True
                            print(f"   ✅ Wallet section clicked via JS XPath")
                    except Exception:
                        pass

                if not wallet_opened:
                    print("   ⚠️  Could not find Wallet section — continuing to label click")

                checkout_page.wait_for_timeout(1500)

                # ── Step 18b: Click the specific label inside Wallet section ──
                print(f"   🏷️  Step 18b: Clicking label inside Wallet section...")
                label_clicked = False

                # Try via JS XPath (bypasses visibility restrictions)
                try:
                    result = checkout_page.evaluate("""
                        (xp) => {
                            var n = document.evaluate(xp, document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (n) { n.click(); return n.innerText.trim() || 'clicked'; }
                            return null;
                        }
                    """, label_xpath)
                    if result:
                        label_clicked = True
                        print(f"   ✅ Label clicked via JS XPath: '{result}'")
                except Exception:
                    pass

                if not label_clicked:
                    print("   ⚠️  Label XPath not found, falling back to EaseMyTrip Wallet label")
                    el_lbl = checkout_page.locator("label.ctr_cbox").filter(has_text="EaseMyTrip Wallet")
                    el_lbl.wait_for(state="attached", timeout=8000)
                    el_lbl.scroll_into_view_if_needed()
                    checkout_page.wait_for_timeout(300)
                    el_lbl.click(force=True)
                    label_clicked = True
                    print(f"   ✅ EaseMyTrip Wallet label clicked via fallback selector")

                checkout_page.wait_for_timeout(1000)
                print(f"   🌐 Page after click: {checkout_page.url}")

            except Exception as e:
                raise RuntimeError(f"❌ Checkout element click failed: {e}")

            # ── Step 19: Capture Total Fare & Click 'Make Payment' ────────
            print(f"\n📌 Step 19: Verifying Total Fare and clicking 'Make Payment'...")
            try:
                # 19a: Read Total Fare on checkout page
                total_fare_raw = None
                try:
                    # Dump all candidate amount elements for debug
                    debug_info = checkout_page.evaluate("""
                        () => Array.from(document.querySelectorAll('span,div,td,strong,p'))
                            .filter(e => {
                                var t = (e.innerText||'').trim();
                                return /[\\u20B9Rs]/.test(t) && /\\d{3,}/.test(t) && t.length < 80;
                            })
                            .slice(0,15)
                            .map(e => '"'+e.className+'" => '+e.innerText.trim().replace(/\\n/g,' | '))
                            .join('\\n')
                    """)
                    print("   🔍 Amount candidates on checkout page:")
                    for line in debug_info.split('\n'):
                        print(f"      {line}")

                    # Target specific Total Fare element
                    total_fare_raw = checkout_page.evaluate("""
                        () => {
                            var selectors = [
                                '.ttl-price', '.total-price', '#totalAmount',
                                '.grand-total-amt', '.totl-fare', '.fare-total',
                                '.checkout-total', '#divTotal', '.amnt-dv',
                                '.pric-blk', '.pric-box'
                            ];
                            for (var s of selectors) {
                                var el = document.querySelector(s);
                                if (el) {
                                    var t = el.innerText.trim();
                                    if (/\\d{3,}/.test(t)) return t;
                                }
                            }
                            // Scan for label+value pairs with "Total Fare"
                            var all = Array.from(document.querySelectorAll('*'));
                            for (var e of all) {
                                var direct = Array.from(e.childNodes)
                                    .filter(n => n.nodeType === 3)
                                    .map(n => n.textContent.trim()).join('');
                                if (/Total Fare|Grand Total/i.test(direct)) {
                                    // Look for sibling/nearby number
                                    var p = e.parentElement;
                                    if (p) {
                                        var m = p.innerText.match(/[\\u20B9Rs.\\s]*([\\d,]{3,}(?:\\.\\d{1,2})?)/);
                                        if (m) return m[0].trim();
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                except Exception:
                    pass

                import re as _re
                if total_fare_raw:
                    total_fare_digits = _re.sub(r'[^\d.]', '', total_fare_raw.strip().split('\n')[-1].strip())
                    print(f"   💰 Total Fare on Checkout Page: {total_fare_raw.strip()} → normalized: ₹{total_fare_digits}")
                else:
                    # Use dt param from URL as fallback (it's base64 of amount in paise or rupees)
                    import base64
                    try:
                        url = checkout_page.url
                        dt_match = _re.search(r'dt=([^&]+)', url)
                        if dt_match:
                            decoded = base64.b64decode(dt_match.group(1) + '==').decode('utf-8')
                            total_fare_digits = decoded.strip()
                            print(f"   💰 Total Fare from URL param (dt): ₹{total_fare_digits}")
                        else:
                            total_fare_digits = None
                            print("   ⚠️  Could not read Total Fare")
                    except Exception:
                        total_fare_digits = None
                        print("   ⚠️  Could not read Total Fare")

                # 19b: Click Make Payment
                clicked = False
                try:
                    result = checkout_page.evaluate("""
                        () => {
                            var els = Array.from(document.querySelectorAll('.mk-pym4'));
                            var el = els.find(e => {
                                var r = e.getBoundingClientRect();
                                return r.width > 0 && r.height > 0 &&
                                       (e.innerText||'').trim() === 'Make Payment';
                            });
                            if (el) { el.click(); return el.outerHTML.substring(0,120); }
                            return null;
                        }
                    """)
                    if result:
                        clicked = True
                        print(f"✅ 'Make Payment' clicked (visible element): {result.strip()}")
                except Exception:
                    pass

                if not clicked:
                    checkout_page.evaluate("document.getElementById('makpbtn').click()")
                    clicked = True
                    print(f"✅ 'Make Payment' clicked via JS on #makpbtn")

                checkout_page.wait_for_timeout(3000)
                print(f"   🌐 URL after Make Payment: {checkout_page.url}")

                # 19c: Read Amount on next/payment page
                payment_amount_digits = None
                try:
                    # Dump all inputs for debug
                    inp_debug = checkout_page.evaluate("""
                        () => Array.from(document.querySelectorAll('input'))
                            .map(e => 'name="'+(e.name||'')+'" id="'+(e.id||'')+'" value="'+(e.value||'')+'"')
                            .join('\\n')
                    """)
                    print("   🔍 Input fields on payment page:")
                    for line in inp_debug.split('\n')[:20]:
                        print(f"      {line}")

                    # Dump visible page text for debug
                    body_text = checkout_page.evaluate("() => document.body.innerText.substring(0, 1000)")
                    print("   🔍 Payment page body text (first 1000 chars):")
                    for line in body_text.split('\n')[:25]:
                        if line.strip():
                            print(f"      {line.strip()}")

                    payment_raw = checkout_page.evaluate("""
                        () => {
                            // 1. Check hidden/visible input fields named 'amount'
                            var inputs = Array.from(document.querySelectorAll('input'));
                            for (var inp of inputs) {
                                var n = (inp.name||inp.id||'').toLowerCase();
                                if (/^(amount|totalamount|txnamount|orderamount|net_amount|order_amount)$/.test(n)) {
                                    if (/^\\d/.test(inp.value)) return inp.value;
                                }
                            }
                            var body = document.body.innerText;
                            // 2. Look for 'Amount : NNNN.NN' pattern (TPSL gateway style)
                            var m = body.match(/Amount\\s*:\\s*([\\d,]+(?:\\.\\d{1,2})?)/i);
                            if (m) return m[1];
                            // 3. Look for INR/Rs/₹ followed by amount
                            var matches = body.match(/(?:INR|Rs\\.?|\\u20B9)\\s*([\\d,]{4,8}(?:\\.\\d{1,2})?)/gi);
                            if (matches) {
                                matches.sort((a,b) => a.length - b.length);
                                return matches[0];
                            }
                            return null;
                        }
                    """)
                    if payment_raw:
                        payment_amount_digits = _re.sub(r'[^\d.]', '', payment_raw)
                        print(f"   💰 Amount on Payment Page: {payment_raw.strip()} → normalized: ₹{payment_amount_digits}")
                    else:
                        print(f"   ⚠️  Could not read amount on payment page")
                except Exception as ex:
                    print(f"   ⚠️  Could not read amount on payment page: {ex}")

                # 19d: Compare and report
                print(f"\n{'─' * 60}")
                if total_fare_digits and payment_amount_digits:
                    # Normalize both to remove leading zeros / trailing .00 differences
                    def _norm(v):
                        try: return str(float(v))
                        except: return v
                    if _norm(total_fare_digits) == _norm(payment_amount_digits):
                        print(f"✅ AMOUNT MATCH — Checkout: {total_fare_digits}  |  Payment Page: {payment_amount_digits}")
                        print(f"✅ TEST CASE PASSED")
                    else:
                        print(f"❌ AMOUNT MISMATCH — Checkout: {total_fare_digits}  |  Payment Page: {payment_amount_digits}")
                        print(f"❌ TEST CASE FAILED")
                        raise RuntimeError(f"Amount mismatch: checkout={total_fare_digits}, payment page={payment_amount_digits}")
                else:
                    print(f"⚠️  Could not fully verify amounts — Checkout: {total_fare_digits}  |  Payment Page: {payment_amount_digits}")
                print(f"{'─' * 60}")

            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"❌ Make Payment / verification failed: {e}")

            # ── Step 20: Click Cancel button on payment page ──────────────
            print(f"\n📌 Step 20: Clicking Cancel button on payment page...")
            try:
                cancel_xpath = "/html/body/form/div/div[3]/div/div[1]/div[2]/div[7]/div[1]/div[2]/div[3]/div/div/a"
                try:
                    checkout_page.wait_for_selector(f"xpath={cancel_xpath}", timeout=10000, state="visible")
                    checkout_page.click(f"xpath={cancel_xpath}")
                    print(f"   ✅ Cancel button clicked via XPath")
                except Exception:
                    # Fallback: JS document.evaluate click
                    result = checkout_page.evaluate(f"""
                        () => {{
                            var result = document.evaluate(
                                "{cancel_xpath}", document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null
                            );
                            var el = result.singleNodeValue;
                            if (el) {{ el.click(); return el.outerHTML.substring(0, 120); }}
                            return null;
                        }}
                    """)
                    if result:
                        print(f"   ✅ Cancel button clicked via JS XPath: {result.strip()}")
                    else:
                        raise RuntimeError("Cancel button element not found via XPath")

                checkout_page.wait_for_timeout(2000)
                print(f"   🌐 URL after Cancel: {checkout_page.url}")

            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"❌ Cancel button click failed: {e}")

            # ── Step 21: Click second Cancel/Back button on payment page ──
            print(f"\n📌 Step 21: Clicking second Cancel/Back button on payment page...")
            try:
                cancel2_xpath = "/html/body/form/div/div[2]/div/div[1]/div[2]/div[3]/div/div/a"
                checkout_page.wait_for_timeout(1500)
                try:
                    checkout_page.wait_for_selector(f"xpath={cancel2_xpath}", timeout=10000, state="visible")
                    checkout_page.click(f"xpath={cancel2_xpath}")
                    print(f"   ✅ Second Cancel/Back button clicked via XPath")
                except Exception:
                    result = checkout_page.evaluate(f"""
                        () => {{
                            var result = document.evaluate(
                                "{cancel2_xpath}", document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null
                            );
                            var el = result.singleNodeValue;
                            if (el) {{ el.click(); return el.outerHTML.substring(0, 120); }}
                            return null;
                        }}
                    """)
                    if result:
                        print(f"   ✅ Second Cancel/Back button clicked via JS XPath: {result.strip()}")
                    else:
                        raise RuntimeError("Second Cancel/Back button element not found via XPath")

                checkout_page.wait_for_timeout(2000)
                print(f"   🌐 URL after Step 21 click: {checkout_page.url}")

            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"❌ Step 21 click failed: {e}")

            # ── Step 22: Capture Booking ID from result page ───────────────
            print(f"\n📌 Step 22: Capturing Booking ID from result page...")
            try:
                booking_id_xpath = "/html/body/form/div[3]/div/div[2]/div[1]/div[2]"
                checkout_page.wait_for_timeout(2000)

                booking_id_text = None
                try:
                    checkout_page.wait_for_selector(f"xpath={booking_id_xpath}", timeout=10000, state="visible")
                    booking_id_text = checkout_page.inner_text(f"xpath={booking_id_xpath}").strip()
                except Exception:
                    booking_id_text = checkout_page.evaluate(f"""
                        () => {{
                            var result = document.evaluate(
                                "{booking_id_xpath}", document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null
                            );
                            var el = result.singleNodeValue;
                            return el ? el.innerText.trim() : null;
                        }}
                    """)

                if booking_id_text:
                    print(f"   🎫 Booking ID: {booking_id_text}")
                    print(f"   ✅ Booking ID captured successfully")
                else:
                    raise RuntimeError("Booking ID element found but text is empty or null")

            except RuntimeError:
                raise
            except Exception as e:
                raise RuntimeError(f"❌ Booking ID capture failed: {e}")

            print("\n✅ All steps completed successfully!")

        except RuntimeError as e:
            print(f"\n{'═' * 60}")
            print(f"❌ STEP FAILED: {e}")
            print(f"{'═' * 60}")
            save_screenshot(page, "failure")

        except Exception as e:
            print(f"\n{'═' * 60}")
            print(f"❌ UNEXPECTED ERROR: {e}")
            print(traceback.format_exc())
            print(f"{'═' * 60}")
            save_screenshot(page, "failure")

        finally:
            # input("\n⏸️  Press Enter to close the browser...")
            browser.close()


if __name__ == "__main__":
    automate_easemytrip()
