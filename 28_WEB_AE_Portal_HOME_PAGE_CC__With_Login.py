"""
EaseMyTrip AE Portal – Hotel Booking Automation (Credit Card, With Login)
URL  : https://www.easemytrip.ae/
Flow : Launch site → click Hotels → login → search Dubai (2 adults) →
       set dates → search → listing → View More → View Rooms →
       Book Now → traveller details → Continue Booking →
       Credit Card payment → OTP page → capture Booking ID
"""

import os
import re
import sys
import datetime

# Force UTF-8 output on Windows (avoids cp1252 emoji encoding errors)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ── Config ─────────────────────────────────────────────────────────────────────
PORTAL_URL     = "https://www.easemytrip.ae/"
HOTELS_URL     = "https://www.easemytrip.ae/hotels/"
LOGIN_EMAIL    = "abhijeet.tiwary@easemytrip.com"
LOGIN_PASSWORD = "Abhijeet9876"

SEARCH_CITY    = "Delhi"
_checkin       = datetime.date.today() + datetime.timedelta(days=2)
_checkout      = datetime.date.today() + datetime.timedelta(days=4)
CHECKIN_STR    = _checkin.strftime("%d/%m/%Y")
CHECKOUT_STR   = _checkout.strftime("%d/%m/%Y")
CHECKIN_DAY    = _checkin.strftime("%d").lstrip("0")
CHECKOUT_DAY   = _checkout.strftime("%d").lstrip("0")
ADULTS         = 2
ROOMS          = 1

FIRST_NAME     = "abhijeet"
LAST_NAME      = "tiwary"
EMAIL          = "abhijeet.tiwary@easemytrip.com"
PHONE          = "8707040722"
PAN_CARD       = "EJDHU3444J"

CARD_NUMBER    = "4992000333871277"
CARD_MM        = "07"
CARD_YY        = "30"
CARD_CVV       = "539"
CARD_NAME      = "Nishant pitti"

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def save_screenshot(page, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        page.screenshot(path=path)
        print(f"📸 Screenshot: {path}")
    except Exception:
        pass


def dom_classes(page):
    """Return all unique CSS class tokens present on the page."""
    try:
        raw = page.evaluate("""(function(){
            var s = new Set();
            document.querySelectorAll('*').forEach(function(el) {
                (el.getAttribute('class') || '').split(' ').forEach(function(c) {
                    if (c.length > 2) s.add(c);
                });
            });
            return Array.from(s).join(' ');
        })()""")
        return raw.split()
    except Exception:
        return []


def click_first_visible(page, selectors, label):
    """Try each selector; click first visible match. Returns selector used or None."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                print(f"✅ {label} clicked via: {sel}")
                return sel
        except Exception:
            continue
    return None


# ── Step 1: Launch site and click Hotels tab ───────────────────────────────────
def step_open_hotels(page):
    print("\n🌐 Launching https://www.easemytrip.ae/ ...")
    page.goto(PORTAL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    print("🏨 Clicking Hotels tab...")
    clicked = click_first_visible(page, [
        'a[href*="/hotels"]',
        'a:has-text("Hotels")',
        ':text("Hotels")',
        '#homepagemenuUL li:nth-child(2) a',
    ], "Hotels tab")

    if not clicked:
        print("⚠️ Hotels tab not found — navigating directly to /hotels/")
        page.goto(HOTELS_URL, wait_until="domcontentloaded")
    else:
        try:
            page.wait_for_url("**/hotels**", timeout=10000)
        except Exception:
            pass

    try:
        page.locator('.htl_location, #txtCity').first.wait_for(state="attached", timeout=15000)
        print(f"✅ Hotels page loaded. URL: {page.url}")
    except Exception:
        raise RuntimeError("❌ Hotels page did not load after clicking Hotels tab.")


# ── Step 2: Login ──────────────────────────────────────────────────────────────
def step_login(page):
    print("\n🔐 Logging in...")

    for sel in ['a._btnclick', '[class*="_btnclick"]', 'a:has-text("Login")']:
        try:
            page.locator(sel).first.hover()
            page.wait_for_timeout(400)
            print(f"✅ Hovered login trigger via: {sel}")
            break
        except Exception:
            continue

    for sel in [':text("Customer Login")', 'a:has-text("Customer Login")', ':text("Sign In")']:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(force=True)
                print(f"✅ Clicked login option via: {sel}")
                break
        except Exception:
            continue

    page.wait_for_timeout(800)

    try:
        page.locator('#txtEmail').fill(LOGIN_EMAIL)
        page.locator('#txtEmail').press('Enter')
        print("✅ Email entered + Enter pressed")
    except Exception as e:
        raise RuntimeError(f"❌ Could not fill email: {e}")

    for sel in ['button:has-text("Continue")', ':text("Continue")', '#btnContinue']:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                try:
                    with page.expect_navigation(timeout=8000, wait_until="domcontentloaded"):
                        el.click()
                except Exception:
                    pass  # no navigation — inline modal
                print("✅ Continue clicked")
                break
        except Exception:
            continue

    # Wait for password field — try longer and with more selectors
    password_filled = False
    import time
    time.sleep(1)   # give Angular/JS time to render password step
    for sel in ['#txtEmail2', '#txtPassword', 'input[type="password"]',
                '[placeholder*="Password"]', '[placeholder*="password"]',
                '[name*="assword"]', '[id*="assword"]']:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=12000)
            el.fill(LOGIN_PASSWORD)
            print("✅ Password entered")
            password_filled = True
            break
        except Exception:
            continue
    if not password_filled:
        # Dump all inputs to understand what state the page is in
        try:
            inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input')).map(el => ({
                id: el.id, name: el.name, type: el.type, ph: el.placeholder,
                vis: el.offsetParent !== null, display: getComputedStyle(el).display
            }))""")
            print(f"🔍 Inputs after Continue: {inputs}")
            print(f"🔍 URL: {page.url}")
            print(f"🔍 Page title: {page.title()}")
        except Exception as ex:
            print(f"⚠️ Dump failed: {ex}")
        raise RuntimeError("❌ Password field not found after Continue")

    for sel in [
        'xpath=/html/body/div[1]/div[1]/div/div/div[2]/div[3]/div/div[5]/input',
        'button:has-text("Login")', ':text("Login")', '#btnLogin',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                try:
                    with page.expect_navigation(timeout=10000, wait_until="domcontentloaded"):
                        el.click()
                except Exception:
                    pass  # no navigation — inline flow
                print("✅ Login clicked")
                break
        except Exception:
            continue

    try:
        page.wait_for_timeout(2000)
    except Exception:
        pass
    print(f"✅ Login done. URL: {page.url}")


# ── Step 3: Navigate to /hotels/ after login ───────────────────────────────────
def step_goto_hotels_after_login(page):
    print(f"\n🏨 Navigating to {HOTELS_URL} after login...")
    page.goto(HOTELS_URL, wait_until="domcontentloaded")
    try:
        page.locator('.htl_location').first.wait_for(state="visible", timeout=15000)
        print("✅ Hotels search form ready")
    except Exception:
        try:
            page.locator('#txtCity').wait_for(state="attached", timeout=8000)
        except Exception:
            raise RuntimeError("❌ Hotels form did not load after login.")
    page.wait_for_timeout(1000)


# ── Step 4: Search city ────────────────────────────────────────────────────────
def step_search_city(page):
    print(f"\n🏙️ Searching for city: {SEARCH_CITY}...")

    try:
        loc = page.locator('.htl_location').first
        if loc.is_visible():
            loc.click()
            page.wait_for_timeout(300)
    except Exception:
        pass

    page.evaluate("""
        var el = document.getElementById('txtCity');
        if (el) {
            el.style.display = 'block';
            el.style.visibility = 'visible';
            el.focus();
        }
    """)
    page.wait_for_timeout(200)

    try:
        city_input = page.locator('#txtCity').first
        city_input.fill("")
        city_input.type("delhi", delay=120)
        print("✅ Typed 'delhi' into city input")
    except Exception as e:
        raise RuntimeError(f"❌ Could not type into city input: {e}")

    try:
        page.locator('#ui-id-1 li.ui-menu-item').first.wait_for(state="visible", timeout=10000)
        print("✅ Autocomplete suggestions appeared")
    except Exception:
        raise RuntimeError("❌ City autocomplete did not appear.")

    items = page.locator('#ui-id-1 li.ui-menu-item').all()
    chosen = None
    for item in items[:6]:
        try:
            text = item.inner_text().lower()
            if "delhi" in text or "new delhi" in text or "india" in text:
                item.click()
                chosen = item.inner_text().split("\n")[0].strip()
                print(f"✅ Selected city: {chosen}")
                break
        except Exception:
            continue

    if not chosen:
        try:
            items[0].click()
            chosen = items[0].inner_text().split("\n")[0].strip()
            print(f"✅ Selected city (fallback): {chosen}")
        except Exception:
            raise RuntimeError("❌ Could not select any city suggestion.")

    page.wait_for_timeout(500)
    return chosen


# ── Step 5: Set check-in / check-out dates ─────────────────────────────────────
def step_set_dates(page):
    print(f"\n📅 Setting dates: {CHECKIN_STR} → {CHECKOUT_STR}...")

    opened = False
    for sel in ['#htl_dates', '#htlcheckIn', '.checkIn', '[id*="htl_dates"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                el.click()
                page.wait_for_timeout(400)
                opened = True
                print(f"✅ Datepicker opened via: {sel}")
                break
        except Exception:
            continue

    if not opened:
        page.evaluate("var el=document.getElementById('htl_dates'); if(el) el.click();")
        page.wait_for_timeout(600)

    try:
        page.locator('#ui-datepicker-div').wait_for(state="visible", timeout=5000)
        ci = page.locator(f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{CHECKIN_DAY}")').first
        ci.wait_for(state="attached", timeout=4000)
        ci.click(force=True)
        page.wait_for_timeout(300)
        print(f"✅ Check-in day {CHECKIN_DAY} selected")

        co = page.locator(f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{CHECKOUT_DAY}")').first
        co.wait_for(state="attached", timeout=4000)
        co.click(force=True)
        page.wait_for_timeout(300)
        print(f"✅ Check-out day {CHECKOUT_DAY} selected")
        return
    except Exception as e:
        print(f"⚠️ Calendar click failed ({e}) — injecting via JS")

    page.evaluate(f"""
        (function(ci, co) {{
            var ciEl = document.getElementById('txtCheckInDate');
            var coEl = document.getElementById('txtCheckOutDate');
            if (ciEl) {{ ciEl.value = ci; ciEl.dispatchEvent(new Event('change', {{bubbles:true}})); }}
            if (coEl) {{ coEl.value = co; coEl.dispatchEvent(new Event('change', {{bubbles:true}})); }}
            if (typeof $ !== 'undefined') {{
                var p = ci.split('/');
                var q = co.split('/');
                try {{
                    $('#txtCheckInDate').datepicker('setDate', new Date(p[2], parseInt(p[1])-1, p[0]));
                    $('#txtCheckOutDate').datepicker('setDate', new Date(q[2], parseInt(q[1])-1, q[0]));
                }} catch(e) {{}}
            }}
        }})('{CHECKIN_STR}', '{CHECKOUT_STR}');
    """)
    page.wait_for_timeout(500)
    print("✅ Dates injected via JS")


# ── Step 6: Set 2 adults ───────────────────────────────────────────────────────
def step_set_adults(page):
    print(f"\n👥 Setting {ADULTS} adults...")

    for sel in ['[class*="roomGuest"]', '#htl_rooms', '#htlRooms']:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                page.wait_for_timeout(400)
                print(f"✅ Rooms panel opened via: {sel}")
                break
        except Exception:
            continue

    for sel in ['[id*="adultPlus"]', '[id*="adult_plus"]',
                '[class*="adult"] button:has-text("+")',
                '[class*="adult"] [class*="plus"]']:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                for _ in range(ADULTS - 1):
                    btn.click()
                    page.wait_for_timeout(200)
                print(f"✅ Adult + clicked {ADULTS-1}x via: {sel}")
                break
        except Exception:
            continue

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    page.wait_for_timeout(300)
    print(f"✅ Guests set ({ADULTS} adults)")


# ── Step 7: Click Search → listing page ───────────────────────────────────────
def step_search(page):
    print("\n🔍 Clicking Search...")

    clicked = click_first_visible(page, [
        'button:has-text("Search")', ':text("Search Hotels")',
        '#btnSearch', '#btnHtlSearch', '[class*="btnsrch"]',
        'button[type="submit"]', 'input[type="submit"]',
    ], "Search button")

    if not clicked:
        try:
            page.evaluate("HotelSearchOffline()")
            print("✅ Search triggered via HotelSearchOffline()")
        except Exception:
            raise RuntimeError("❌ Could not trigger hotel search.")

    try:
        page.wait_for_url(lambda u: "hotel-new/search" in u, timeout=20000)
        print(f"✅ Results URL: {page.url}")
    except PlaywrightTimeoutError:
        page.wait_for_timeout(3000)
        if "hotel-new/search" not in page.url:
            raise RuntimeError(f"❌ Search did not navigate to results. URL: {page.url}")

    # Ensure pax=2 in URL
    current = page.url
    if "pax=" in current and f"pax={ADULTS}" not in current:
        fixed = re.sub(r'pax=\d+', f'pax={ADULTS}', current)
        page.goto(fixed, wait_until="domcontentloaded")
        print(f"✅ URL updated to pax={ADULTS}: {page.url}")


# ── Step 8: Verify hotel listings ─────────────────────────────────────────────
def step_check_listings(page):
    print("\n🔎 Checking hotel listings...")
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    for sel in ['.listing-bx', '.htl_name', '.htl-nm', '.htlinfo',
                '[class*="htlname"]', '[class*="hotel-name"]']:
        count = page.locator(sel).count()
        if count > 0:
            print(f"✅ {count} hotel(s) found via: {sel}")
            return

    page_text = page.inner_text("body").lower()
    for kw in ['no hotel', 'no result', '0 hotel']:
        if kw in page_text:
            raise RuntimeError(f"❌ No hotels found — page shows '{kw}'.")
    raise RuntimeError("❌ No hotel listing cards detected.")


# ── Step 9: Click View More (if present) ──────────────────────────────────────
def step_view_more(page):
    print("\n🔽 Looking for 'View More' button...")
    page.evaluate("window.scrollBy(0, 300)")
    page.wait_for_timeout(400)

    clicked = click_first_visible(page, [
        '.listing-bx a:has-text("View More")',
        '.listing-bx button:has-text("View More")',
        '.listing-footer a:has-text("View More")',
        'a:has-text("View More")',
        'button:has-text("View More")',
        ':text("View More")',
    ], "'View More'")

    if not clicked:
        print("ℹ️ No 'View More' button found — proceeding")


# ── Step 10: Click a random View Rooms button (opens new tab) ─────────────────
def step_view_rooms(page):
    import random
    print("\n🛏️ Collecting all 'View Rooms' buttons for random selection...")
    page.wait_for_timeout(500)
    page.evaluate("window.scrollBy(0, 300)")
    page.wait_for_timeout(300)

    # Gather all visible "View Rooms" elements across multiple selectors
    candidates = []
    for sel in [
        '.listing-bx button:has-text("View Rooms")',
        '.listing-bx a:has-text("View Rooms")',
        '.listing-footer button:has-text("View Rooms")',
        '.listing-footer a:has-text("View Rooms")',
        'button:has-text("View Rooms")',
        'a:has-text("View Rooms")',
    ]:
        try:
            for el in page.locator(sel).all():
                try:
                    if el.is_visible():
                        candidates.append(el)
                except Exception:
                    continue
        except Exception:
            continue

    # De-duplicate by pixel position so the same element found via multiple
    # selectors is not counted twice.
    seen_positions = set()
    unique_candidates = []
    for el in candidates:
        try:
            bb = el.bounding_box()
            if bb:
                key = (round(bb['x']), round(bb['y']))
                if key not in seen_positions:
                    seen_positions.add(key)
                    unique_candidates.append(el)
        except Exception:
            continue

    # Role-based fallback if nothing found yet
    if not unique_candidates:
        try:
            for el in page.get_by_role("button", name="View Rooms").all():
                try:
                    if el.is_visible():
                        unique_candidates.append(el)
                except Exception:
                    continue
        except Exception:
            pass

    if not unique_candidates:
        raise RuntimeError("❌ No 'View Rooms' buttons found on the listing page.")

    # Pick one at random and click it
    btn = random.choice(unique_candidates)
    chosen_idx = unique_candidates.index(btn) + 1
    print(f"🎲 Randomly selected 'View Rooms' button #{chosen_idx} of {len(unique_candidates)} available")

    try:
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
    except Exception:
        pass

    try:
        with page.context.expect_page(timeout=12000) as np_info:
            btn.click()
        new_page = np_info.value
        new_page.wait_for_load_state("domcontentloaded")
        print(f"✅ 'View Rooms' clicked. New tab: {new_page.url}")
        return new_page
    except Exception as e:
        raise RuntimeError(f"❌ Could not click 'View Rooms' button: {e}")


# ── Step 11: Click Book Now ────────────────────────────────────────────────────
def step_book_now(page):
    import time
    print("\n📋 Clicking 'Book Now'...")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    time.sleep(2)

    # Dump visible anchor/button text for diagnosis
    try:
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a,button'))
            .filter(el => el.offsetParent !== null)
            .map(el => el.innerText.trim().slice(0, 40))
            .filter(t => t.length > 0)
        """)
        print(f"🔍 Visible links/buttons: {links[:20]}")
    except Exception:
        pass

    clicked = click_first_visible(page, [
        'a:has-text("Book Now")', 'button:has-text("Book Now")',
        ':text("Book Now")', ':text("BOOK NOW")',
        'a:has-text("Book")', '[class*="book-now"]', '[class*="bookNow"]',
        '[class*="bkbtn"]', '[class*="bookbtn"]',
    ], "'Book Now'")

    if not clicked:
        # JS fallback — scroll + click first visible anchor containing "Book"
        try:
            result = page.evaluate("""() => {
                var els = Array.from(document.querySelectorAll('a,button'));
                var el = els.find(e => /book/i.test(e.innerText));
                if (el) { el.scrollIntoView({block:'center'}); el.click(); return el.innerText.trim(); }
                return null;
            }""")
            if result:
                print(f"✅ 'Book Now' clicked via JS fallback: {result}")
                time.sleep(1500)
                print(f"📄 URL: {page.url}")
                return
        except Exception:
            pass
        raise RuntimeError("❌ Could not find 'Book Now' button.")

    time.sleep(2)
    print(f"📄 URL: {page.url}")


# ── Step 12: Read Grand Total ─────────────────────────────────────────────────
def step_read_grand_total(page, label=""):
    tag = f" ({label})" if label else ""
    print(f"\n💰 Reading Grand Total{tag}...")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    currency_re = re.compile(
        r'(?:AED|Dhs|د\.إ|₹|INR|Rs\.?)\s*[\d,]+(?:\.\d+)?'
        r'|[\d,]+(?:\.\d+)?\s*(?:AED|Dhs|د\.إ)',
        re.IGNORECASE
    )

    for sel in ['[class*="grand-total"]', '[class*="grandTotal"]', '[class*="totalAmt"]',
                '[class*="payable"]', '[id*="grandTotal"]', '[id*="totalAmt"]',
                'td:has-text("Grand Total")', 'div:has-text("Grand Total")']:
        try:
            for el in page.locator(sel).all():
                m = currency_re.search(el.inner_text())
                if m:
                    total = m.group(0).strip()
                    print(f"✅ Grand Total{tag}: {total}")
                    return total
        except Exception:
            continue

    try:
        m = currency_re.search(page.inner_text("body"))
        if m:
            total = m.group(0).strip()
            print(f"✅ Grand Total{tag} (body): {total}")
            return total
    except Exception:
        pass

    print(f"⚠️ Grand Total not found{tag}")
    return "N/A"


# ── Step 13: Fill traveller details ───────────────────────────────────────────
def step_fill_traveller(page):
    print("\n✍️ Filling traveller details...")
    page.wait_for_timeout(1000)

    def fill(selectors, value, name):
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    el.fill(value)
                    print(f"✅ {name} filled")
                    return
            except Exception:
                continue
        print(f"⚠️ Could not fill {name}")

    fill(['[name=txtFirstName]', '#txtFirstName', '[placeholder*="First"]',
          '[placeholder*="first"]'], FIRST_NAME, "First name")
    fill(['[name=txtLastName]', '#txtLastName', '[placeholder*="Last"]',
          '[placeholder*="last"]'], LAST_NAME, "Last name")
    fill(['[name=txtEmail]', '#txtEmailId', '[type="email"]',
          '[placeholder*="Email"]', '[placeholder*="email"]'], EMAIL, "Email")
    fill(['[name=txtMobile]', '#txtMobile', '[placeholder*="Mobile"]',
          '[placeholder*="mobile"]', '[placeholder*="Phone"]',
          '[placeholder*="phone"]'], PHONE, "Phone")
    fill(['[name=txtPanNo]', '#txtPanNo', '[placeholder*="PAN"]',
          '[placeholder*="Pan"]', '[placeholder*="pan"]',
          '[name*="pan"]', '[id*="pan"]', '[id*="Pan"]'], PAN_CARD, "PAN card")


# ── Step 14: Continue Booking ─────────────────────────────────────────────────
def step_continue_booking(page):
    print("\n🔘 Clicking 'Continue Booking'...")
    try:
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Find button first before clicking
    btn = None
    for sel in [
        'button:has-text("Continue Booking")',
        'a:has-text("Continue Booking")',
        ':text("Continue Booking")',
        ':text("Proceed to Payment")',
        'button:has-text("Proceed")',
        'button[type="submit"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                btn = el
                print(f"✅ Found via: {sel}")
                break
        except Exception:
            continue

    if not btn:
        raise RuntimeError("❌ Could not find 'Continue Booking' button.")

    # Click while watching for new tab (payment gateway may open a new tab)
    try:
        with page.context.expect_page(timeout=8000) as new_page_info:
            btn.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded", timeout=20000)
        print(f"✅ 'Continue Booking' → new tab: {new_page.url}")
        return new_page
    except Exception:
        # No new tab — inline SPA transition on same page
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass
        try:
            print(f"📄 URL after Continue: {page.url}")
        except Exception:
            pass
        return page


# ── Step 15: Select Credit Card payment option ────────────────────────────────
def step_select_credit_card(page):
    import time
    print("\n💳 Selecting Credit/Debit Card payment...")
    time.sleep(3)   # use time.sleep to avoid TargetClosedError from page.wait_for_timeout

    try:
        classes = dom_classes(page)
        pay_cls = [c for c in classes if any(k in c.lower() for k in
                   ('pay', 'card', 'credit', 'debit', 'pg', 'upi', 'net', 'wallet'))]
        print(f"💳 Payment classes: {pay_cls[:30]}")
    except Exception as e:
        print(f"⚠️ Could not dump classes: {e}")

    for sel in [
        '.card.PG',
        'text="Credit/Debit/ATM Cards"',
        'text="Credit / Debit Card"',
        'text="Credit/Debit Card"',
        ':text("Credit Card")',
        ':text("Debit Card")',
        ':text("Credit/Debit")',
        '[class*="card"][class*="PG"]',
        '[class*="card-pay"]', '[class*="creditCard"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                print(f"✅ Credit Card option clicked via: {sel}")
                time.sleep(2)
                try:
                    page.wait_for_selector(
                        '[placeholder*="Card"],[id*="cardNo"],[name*="cardNo"],[id*="CardNo"]',
                        state="visible", timeout=8000
                    )
                except Exception:
                    pass
                print(f"📄 URL: {page.url}")

                # Dump card form classes for debugging
                try:
                    classes2 = dom_classes(page)
                    card_cls = [c for c in classes2 if any(k in c.lower() for k in
                                ('card', 'cvv', 'expir', 'valid', 'holder', 'pan'))]
                    print(f"💳 Card-form classes after click: {card_cls[:30]}")
                except Exception:
                    pass
                return
        except Exception:
            continue

    raise RuntimeError("❌ Credit Card payment option not found.")


# ── Step 16: Fill card details ────────────────────────────────────────────────
def _get_payment_ctx(page):
    try:
        for frame in page.frames:
            url = frame.url or ""
            if url and "easemytrip" not in url and url != "about:blank":
                if frame.locator('input').count() > 0:
                    print(f"💳 Payment iframe: {url[:70]}")
                    return frame
    except Exception:
        pass
    return page


def step_fill_card(page):
    print("\n💳 Filling card details...")
    ctx = _get_payment_ctx(page)

    # Dump ALL input fields for diagnosis
    try:
        inputs_info = page.evaluate("""(function(){
            return Array.from(document.querySelectorAll('input')).map(function(i){
                return {id:i.id, name:i.name, ph:i.placeholder, type:i.type, vis:(i.offsetParent!==null)};
            });
        })()""")
        visible_inputs = [x for x in inputs_info if x.get('vis')]
        print(f"💳 Visible inputs: {visible_inputs[:15]}")
    except Exception:
        pass

    def fill_by_attrs(id_fragments, ph_fragments, value, field_name):
        # By placeholder
        for ph in ph_fragments:
            try:
                el = ctx.get_by_placeholder(ph).first
                if el.count() > 0 and el.is_visible():
                    el.fill(value)
                    print(f"✅ {field_name} filled via placeholder '{ph}'")
                    return True
            except Exception:
                continue
        # By id/name
        for frag in id_fragments:
            for attr in ('id', 'name'):
                try:
                    el = ctx.locator(f'[{attr}*="{frag}"]').first
                    if el.count() > 0 and el.is_visible():
                        el.fill(value)
                        print(f"✅ {field_name} filled via [{attr}*='{frag}']")
                        return True
                except Exception:
                    continue
        print(f"⚠️ Could not fill {field_name}")
        return False

    fill_by_attrs(
        ['cardNumber', 'cardNo', 'CardNo', 'CardNumber', 'pan', 'PAN', 'card-input'],
        ['Card Number', 'card number', 'Enter Card Number', 'ENTER CARD NUMBER', 'Card No', 'PAN'],
        CARD_NUMBER, "Card Number"
    )
    # Fill MM/YY as combined value (e.g. "07/30") — portal uses single MM/YY field
    mmyy_filled = fill_by_attrs(
        ['CCMM', 'expiry', 'expDate', 'cardExpiry', 'mmyy'],
        ['MM/YY', 'MM / YY', 'Expiry', 'MMYY'],
        f"{CARD_MM}/{CARD_YY}", "Expiry MM/YY"
    )
    if not mmyy_filled:
        # Fallback: fill month and year separately
        fill_by_attrs(
            ['expMonth', 'ExpMonth', 'cardMM', 'cardMonth'],
            ['MM', 'Month', 'Expiry Month', 'Exp Month'],
            CARD_MM, "Expiry Month"
        )
        fill_by_attrs(
            ['expYear', 'ExpYear', 'cardYY', 'cardYear'],
            ['YY', 'Year', 'Expiry Year', 'YYYY', 'Exp Year'],
            CARD_YY, "Expiry Year"
        )
    fill_by_attrs(
        ['cvv', 'CVV', 'cvc', 'CVC', 'securityCode'],
        ['CVV', 'cvv', 'CVV/CVC', 'Security Code'],
        CARD_CVV, "CVV"
    )
    fill_by_attrs(
        ['cardHolder', 'CardHolder', 'nameOnCard', 'NameOnCard', 'cardName'],
        ['Card Holder Name', 'Name on Card', 'Cardholder Name', 'Name As on Card', 'Name'],
        CARD_NAME, "Card Holder Name"
    )


# ── Step 17: Make Payment ─────────────────────────────────────────────────────
def step_make_payment(page):
    import time
    print("\n🚀 Clicking 'Make Payment'...")

    # Dump ALL pay-related elements (not filtered by visibility) for diagnosis
    try:
        btns = page.evaluate("""() => Array.from(document.querySelectorAll(
            '[class*="payGT"],[class*="pay-btn"],[class*="paybtn"],button,[type="submit"],input[type="submit"]'))
            .map(el => ({tag: el.tagName, text: el.innerText.trim().slice(0,60), cls: el.className.slice(0,80),
                         vis: el.offsetParent !== null, display: getComputedStyle(el).display}))
        """)
        print(f"🔍 Pay elements: {btns[:20]}")
    except Exception:
        pass

    # Primary: invoke CardValidationV1 via Angular $scope (proper AngularJS trigger)
    try:
        result = page.evaluate("""() => {
            var el = document.querySelector('div.mk-pym');
            if (el) {
                try {
                    var scope = angular.element(el).scope();
                    scope.$apply(function() { scope.CardValidationV1(scope.engine); });
                    return 'angular-scope';
                } catch(e) {}
                // Fallback: dispatch MouseEvent so Angular's event listener fires
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
                return 'dispatch-click';
            }
            return null;
        }""")
        if result:
            print(f"✅ Make Payment triggered via: {result}")
            # Wait for navigation to OTP/3DS/bank page
            try:
                page.wait_for_url(
                    lambda url: "otp" in url.lower() or "validation" in url.lower()
                                or "3ds" in url.lower() or "secure" in url.lower()
                                or "corporatevalidation" in url.lower()
                                or "bank" in url.lower(),
                    timeout=20000
                )
            except Exception:
                pass
            time.sleep(2)
            print(f"📄 URL: {page.url}")
            return
    except Exception as e:
        print(f"⚠️ Angular $scope click failed: {e}")

    raise RuntimeError("❌ Could not trigger Make Payment.")


# ── Step 18: OTP page ─────────────────────────────────────────────────────────
def step_otp_page(page):
    print("\n🔑 Handling OTP page...")
    # Only wait for navigation if still on checkout page
    try:
        if "checkout" in page.url.lower():
            page.wait_for_url(
                lambda url: "otp" in url.lower() or "validation" in url.lower()
                            or "3ds" in url.lower() or "secure" in url.lower()
                            or "corporatevalidation" in url.lower()
                            or "bank" in url.lower() or "m2p" in url.lower()
                            or "acsv2" in url.lower() or "emv" in url.lower()
                            or "auth" in url.lower() or "acq" in url.lower(),
                timeout=20000
            )
    except Exception:
        pass

    try:
        page.wait_for_timeout(1000)
        print(f"📄 URL: {page.url}")
    except Exception as e:
        print(f"⚠️ OTP page closed early: {e}")
        return

    try:
        m = re.search(r'(?:AED|Dhs|₹|INR)\s*[\d,]+(?:\.\d+)?', page.inner_text("body"))
        if m:
            print(f"💰 Amount on OTP page: {m.group(0)}")
    except Exception:
        pass

    # Click Cancel Payment button then confirm with Yes
    print("🚫 Clicking 'Cancel Payment'...")
    try:
        cancel_btn = page.locator('xpath=/html/body/div[1]/div[1]/footer/div[2]/p').first
        cancel_btn.wait_for(state="visible", timeout=10000)
        cancel_btn.click()
        print("✅ Cancel Payment clicked")
        page.wait_for_timeout(1500)
    except Exception as e:
        print(f"⚠️ Cancel Payment click failed: {e}")

    print("✅ Clicking 'Yes' to confirm cancellation...")
    try:
        clicked = click_first_visible(page, [
            'button:has-text("Yes")', ':text("Yes")',
            'a:has-text("Yes")', '[ng-click*="yes"]',
        ], "Yes button")
        if clicked:
            page.wait_for_timeout(2000)
    except Exception as e:
        print(f"⚠️ Yes button click failed: {e}")


# ── Step 19: Capture Booking ID ───────────────────────────────────────────────
def step_capture_booking_id(page):
    print("\n🎫 Capturing Booking ID...")
    page.wait_for_timeout(3000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    try:
        body = page.inner_text("body")
        for pat in [
            r'Booking\s*(?:ID|No\.?|Number)[:\s#]*([A-Z0-9\-]+)',
            r'Confirmation\s*(?:No\.?|Number)[:\s#]*([A-Z0-9\-]+)',
            r'(?:EMT|HTL|BKG)[A-Z0-9\-]+',
        ]:
            m = re.search(pat, body, re.IGNORECASE)
            if m:
                bid = m.group(1) if m.lastindex else m.group(0)
                print(f"🎉 Booking ID: {bid}")
                return bid
    except Exception:
        pass

    print(f"⚠️ Booking ID not found. URL: {page.url}")
    save_screenshot(page, "booking_confirmation")
    return None


# ── Main ──────────────────────────────────────────────────────────────────────
def automate_easemytrip_ae():
    print("=" * 65)
    print("  EaseMyTrip AE – Hotel Booking (CC, With Login)")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        hotel_page = None

        try:
            step_open_hotels(page)
            step_login(page)
            step_goto_hotels_after_login(page)
            city = step_search_city(page)
            step_set_dates(page)
            step_set_adults(page)
            step_search(page)
            step_check_listings(page)
            step_view_more(page)
            hotel_page = step_view_rooms(page)
            step_book_now(hotel_page)
            total_traveller = step_read_grand_total(hotel_page, "Traveller Page")
            step_fill_traveller(hotel_page)
            payment_page = step_continue_booking(hotel_page)
            total_checkout = step_read_grand_total(payment_page, "Checkout Page")

            def norm(s):
                return re.sub(r'[^\d.]', '', s or '')
            if norm(total_traveller) and norm(total_checkout) and norm(total_traveller) != norm(total_checkout):
                print(f"⚠️ Grand Total mismatch: {total_traveller} vs {total_checkout}")
            else:
                print(f"✅ Grand Total OK: {total_traveller}")

            step_select_credit_card(payment_page)
            step_fill_card(payment_page)
            step_make_payment(payment_page)
            step_otp_page(payment_page)
            booking_id = step_capture_booking_id(payment_page)

            print("\n" + "=" * 65)
            print("✅ AUTOMATION COMPLETE")
            if booking_id:
                print(f"   Booking ID : {booking_id}")
            print(f"   City       : {city}")
            print(f"   Dates      : {CHECKIN_STR} → {CHECKOUT_STR}")
            print(f"   Adults     : {ADULTS}")
            print("=" * 65)

        except RuntimeError as e:
            print(f"\n❌ FAILED: {e}")
            save_screenshot(hotel_page if hotel_page else page, "failure_ae")
        except Exception as e:
            import traceback
            print(f"\n❌ UNEXPECTED ERROR: {e}")
            traceback.print_exc()
            save_screenshot(hotel_page if hotel_page else page, "failure_ae")
        finally:
            browser.close()


if __name__ == "__main__":
    automate_easemytrip_ae()
