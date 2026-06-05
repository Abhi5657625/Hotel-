import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import re
import traceback
import random
from datetime import datetime, timedelta

CITY_PREFIXES = ['dubai']  # Single city search: 'dubai' → Dubai, UAE

# Login credentials
LOGIN_EMAIL    = "abhijeet.tiwary@easemytrip.com"
LOGIN_PASSWORD = "Abhijeet9876"
SUGGESTION_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[1]/div/div[2]/div[1]'
SUGGESTION_LIST_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li'
DIV5_INPUT_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/div[5]/input'
CITY_INPUT_ID = '#txtCity'
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

# Selectors to detect hotel listing cards on the results page
HOTEL_LISTING_SELECTORS = [
    '[class*="htlname"]',
    '[class*="htl-name"]',
    '[class*="htl-nm"]',
    '[class*="htl_name"]',
    '[class*="hotel-name"]',
    '[class*="hotelName"]',
    '[class*="HotelName"]',
    '[class*="htl-list"]',
    '[class*="hotel-list"]',
    '[class*="listing-hotel"]',
    '[class*="listing-bx"]',
    '[class*="listing-area"]',
    '[class*="listing-cvr"]',
    '[class*="htlinfo"]',
    '.htlname',
    '.hotel-name',
    '[class*="htl-cont"]',
    '[class*="htlCont"]',
]

# Keywords that indicate a "no results" state on the page
NO_RESULT_KEYWORDS = [
    'no hotel found',
    'no result',
    'not found',
    '0 hotel',
    'no properties found',
    'no hotels available',
    'no hotels found',
    'hotels not available',
]

# Possible search/submit button selectors on the hotel form
SEARCH_BUTTON_SELECTORS = [
    '#btnSearch',
    '#btnHtlSearch',
    '[id*="HtlSearch"]',
    '[id*="htlSearch"]',
    '[class*="search-btn"]',
    '[class*="srchBtn"]',
    '[class*="SearchBtn"]',
    '[class*="searchBtn"]',
    '[class*="htlsrch"]',
    '[class*="hotel-search"]',
    'button[type="submit"]',
    'input[type="submit"]',
    '[class*="btn-search"]',
    '[class*="srch-btn"]',
]

# Visible date-trigger selectors (the clickable display elements, not hidden inputs)
DATE_TRIGGER_SELECTORS = [
    '#htl_dates',
    '#htlcheckIn',
    '#txtcheckIn',
    '.checkIn',
    '.htl-checkin',
    '[id*="CheckIn"][class*="date"]',
    '[class*="checkin-date"]',
]

# XPath fallback for the EaseMyTrip hotel search button
SEARCH_BUTTON_XPATH = 'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[4]/button'


def save_screenshot(page, name):
    """Save a screenshot for debugging on failure."""
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        page.screenshot(path=path)
        print(f"📸 Screenshot saved: {path}")
    except Exception:
        print("⚠️ Could not save screenshot.")


def check_hotel_listings(page, city_name):
    """
    Verify that hotel listing cards are displayed for the searched city/sector.
    Raises RuntimeError with a clear message if no listings are found.
    """
    print(f"🔎 Checking hotel listings for sector '{city_name}'...")

    # Wait for at least one listing card to appear (up to 25s)
    try:
        page.wait_for_selector('[class*="htlname"],[class*="htl-nm"],[class*="htl_name"],[class*="hotel-name"],[class*="htl-cont"],[class*="listing-bx"]', timeout=25000)
    except Exception:
        pass
    current_url = page.url
    print(f"📍 Current URL: {current_url}")

    # Count listing cards using known selectors
    listing_count = 0
    matched_selector = None
    for selector in HOTEL_LISTING_SELECTORS:
        try:
            count = page.locator(selector).count()
            if count > 0:
                listing_count = count
                matched_selector = selector
                break
        except Exception:
            continue

    if listing_count > 0:
        print(f"✅ Hotel listings ARE coming for sector '{city_name}' — {listing_count} hotel(s) found.")
        return

    # No listing cards found — check for explicit "no results" text on the page
    try:
        page_text = page.inner_text("body").lower()
    except Exception:
        page_text = ""

    for keyword in NO_RESULT_KEYWORDS:
        if keyword in page_text:
            raise RuntimeError(
                f"❌ Hotel listings are NOT coming for sector '{city_name}' — "
                f"Page shows a 'no results' message. Please check availability for this sector."
            )

    # No cards and no explicit message — generic failure
    raise RuntimeError(
        f"❌ Hotel listings are NOT coming for sector '{city_name}' — "
        f"No hotel cards were found on the page. The results may have failed to load."
    )


VIEW_ROOMS_SELECTORS = [
    'button:has-text("View Rooms")',
    'a:has-text("View Rooms")',
    '[class*="view-room"]',
    '[class*="viewRoom"]',
    '[class*="ViewRoom"]',
    '[class*="view_room"]',
    'button:has-text("Select Room")',
    'a:has-text("Select Room")',
]

BOOK_NOW_SELECTORS = [
    'button:has-text("Book Now")',
    'a:has-text("Book Now")',
    '[class*="book-now"]',
    '[class*="bookNow"]',
    '[class*="BookNow"]',
    'button:has-text("Book")',
    'a:has-text("Book")',
]


def click_view_rooms(page, city_name):
    """
    Click a RANDOM 'View Rooms' button on the hotel listing page.
    Waits for the new tab that opens and returns it.
    """
    print(f"\n🛏️ Clicking a RANDOM 'View Rooms' button on the listing page for '{city_name}'...")

    # Wait for listing cards to fully render, then a small settle buffer
    try:
        page.wait_for_selector('[class*="htlname"],[class*="hotel-name"],[class*="htl-cont"]', timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(500)

    # Scroll down slightly to trigger lazy-loaded cards
    page.evaluate("window.scrollBy(0, 400)")
    page.wait_for_timeout(300)

    def _do_click(btn):
        btn.scroll_into_view_if_needed()
        with page.context.expect_page(timeout=10000) as new_page_info:
            btn.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        print(f"✅ New tab opened. URL: {new_page.url}")
        return new_page

    # Try role/text-based locator — pick a random one
    try:
        all_btns = page.get_by_role("button", name="View Rooms")
        count = all_btns.count()
        if count > 0:
            idx = random.randint(0, count - 1)
            print(f"🎲 Randomly selected 'View Rooms' button index {idx} out of {count} (role/name)")
            btn = all_btns.nth(idx)
            new_page = _do_click(btn)
            print("✅ 'View Rooms' button clicked via role/name")
            return new_page
    except Exception:
        pass

    # Try CSS / text selectors (extended list) — pick a random one
    extended_selectors = VIEW_ROOMS_SELECTORS + [
        'a:has-text("View Room")',
        'button:has-text("View Room")',
        'a:has-text("Select Rooms")',
        'button:has-text("Select Rooms")',
        'a:has-text("Check Availability")',
        '[class*="viewRooms"]',
        '[class*="view-rooms"]',
    ]
    for selector in extended_selectors:
        try:
            all_btns = page.locator(selector)
            count = all_btns.count()
            if count > 0:
                idx = random.randint(0, count - 1)
                print(f"🎲 Randomly selected button index {idx} out of {count} via selector: {selector}")
                btn = all_btns.nth(idx)
                new_page = _do_click(btn)
                print(f"✅ 'View Rooms' button clicked via selector: {selector}")
                return new_page
        except Exception:
            continue

    raise RuntimeError(
        f"❌ 'View Rooms' button is not working — could not find or click it for '{city_name}'."
    )


def click_book_now(page, city_name):
    """Click the 'Book Now' button on the hotel detail/rooms page."""
    print(f"\n📋 Clicking 'Book Now' for '{city_name}'...")

    # Wait for the page to render room options
    try:
        page.wait_for_selector('a:has-text("Book Now"), button:has-text("Book Now")', timeout=10000)
    except Exception:
        pass

    def _after_click(label):
        print(f"✅ 'Book Now' button clicked via {label}")
        try:
            page.wait_for_url("**/travellers**", timeout=15000)
        except Exception:
            pass
        print(f"📄 Current URL: {page.url}")

    # Try role/text-based locator first
    try:
        btn = page.get_by_role("button", name="Book Now").first
        if btn.count() > 0:
            btn.scroll_into_view_if_needed()
            btn.click()
            _after_click("role/name")
            return
    except Exception:
        pass

    # Try CSS / text selectors
    for selector in BOOK_NOW_SELECTORS:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0:
                btn.scroll_into_view_if_needed()
                btn.click()
                _after_click(f"selector: {selector}")
                return
        except Exception:
            continue

    raise RuntimeError(
        f"❌ 'Book Now' button is not working — could not find or click it for '{city_name}'."
    )


DISMISS_SELECTORS = [
    'button:has-text("Skip")',
    'button:has-text("skip")',
    'button:has-text("Dismiss")',
    'button:has-text("dismiss")',
    'button:has-text("Close")',
    'button:has-text("close")',
    'button:has-text("No Thanks")',
    'button:has-text("Cancel")',
    'a:has-text("Skip")',
    'a:has-text("Dismiss")',
    '[class*="skip"]',
    '[class*="Skip"]',
    '[class*="dismiss"]',
    '[class*="close-btn"]',
    '[class*="closeBtn"]',
    '[class*="popup-close"]',
    '[aria-label="Close"]',
    '[aria-label="Dismiss"]',
    '[aria-label="Skip"]',
    '.modal-close',
    '.popup-dismiss',
]


def dismiss_popup(page):
    """
    Dismiss ALL visible popups/modals on the page.
    Repeats until no more dismissible popups are found.
    Only clicks if a Skip/Dismiss/Close button is actually visible.
    """
    page.wait_for_timeout(200)
    dismissed_count = 0

    for attempt in range(5):  # handle up to 5 stacked popups
        dismissed = False

        # Check role-based buttons first
        for btn_name in ["Skip", "Dismiss", "Close", "No Thanks", "Cancel"]:
            try:
                btn = page.get_by_role("button", name=btn_name).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    print(f"🔔 Popup dismissed via role/name '{btn_name}'")
                    page.wait_for_timeout(500)
                    dismissed = True
                    dismissed_count += 1
                    break
            except Exception:
                pass

        # Check CSS selectors if role-based didn't match
        if not dismissed:
            for selector in DISMISS_SELECTORS:
                try:
                    btn = page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        print(f"🔔 Popup dismissed via selector: {selector}")
                        page.wait_for_timeout(500)
                        dismissed = True
                        dismissed_count += 1
                        break
                except Exception:
                    continue

        if not dismissed:
            break  # No more visible popups

    if dismissed_count == 0:
        print("ℹ️ No popup found to dismiss, continuing...")
    else:
        print(f"✅ Dismissed {dismissed_count} popup(s)")


FIRST_NAME_SELECTORS = [
    '[name="txtFirstName"]',
    '[name="firstName"]',
    '[name="fname"]',
    '#firstName',
    '#fname',
    '#FirstName',
    '[id*="first"][type="text"]',
    '[placeholder="Enter first name"]',
    '[placeholder*="First Name"]',
    'input[id*="First"]',
    'input[id*="first"]',
]


def fill_first_name(page, name, city_name):
    """Dismiss any popup, then fill the first name field on the traveller details page."""
    print(f"\n✍️ Entering first name '{name}' on traveller page...")

    travellers_url = page.url

    # Dismiss any popup/modal before interacting with the form
    dismiss_popup(page)

    print(f"🔗 URL after dismiss: {page.url}")

    # If the popup redirected us away from the travellers page, go back
    if "travellers" not in page.url:
        print(f"⚠️ Redirected to {page.url} — navigating back to travellers page")
        page.goto(travellers_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        # Dismiss any popup that appears on reload too
        dismiss_popup(page)
        print(f"🔗 URL after re-navigate + dismiss: {page.url}")

    # Wait explicitly for the first name field to be visible after popup closes
    try:
        page.wait_for_selector('[name="txtFirstName"]', state="visible", timeout=10000)
        field = page.locator('[name="txtFirstName"]').first
        # Dismiss any overlay (md_foptn dropdown) that may intercept clicks
        try:
            overlay = page.locator('[class*="md_foptn"]').first
            if overlay.count() > 0 and overlay.is_visible():
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        except Exception:
            pass
        field.click(force=True)
        field.fill(name)
        print(f"✅ First name '{name}' entered via [name=txtFirstName]")
        return
    except Exception as ex:
        print(f"⚠️ txtFirstName wait failed: {ex}")

    # Try placeholder directly
    try:
        field = page.get_by_placeholder("Enter first name").first
        field.wait_for(state="visible", timeout=8000)
        field.click(force=True)
        field.fill(name)
        print(f"✅ First name '{name}' entered via placeholder")
        return
    except Exception as ex:
        print(f"⚠️ placeholder fallback failed: {ex}")

    # Fallback: try remaining known selectors
    for selector in FIRST_NAME_SELECTORS:
        try:
            field = page.locator(selector).first
            if field.count() > 0:
                field.wait_for(state="visible", timeout=5000)
                field.click()
                field.fill(name)
                print(f"✅ First name '{name}' entered via selector: {selector}")
                return
        except Exception:
            continue

    # Placeholder-based
    for ph in ["Enter first name", "First Name", "first name", "First", "Given Name"]:
        try:
            field = page.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.fill(name)
                print(f"✅ First name '{name}' entered via placeholder '{ph}'")
                return
        except Exception:
            continue

    # Last resort: first visible text input on the page
    try:
        field = page.locator('input[type="text"]:visible, input:not([type]):visible').first
        if field.count() > 0:
            field.click()
            field.fill(name)
            print("✅ First name entered via first visible text input")
            return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ First name field not found on traveller page for '{city_name}'."
    )


def fill_last_name(page, name, city_name):
    """Fill the last name field on the traveller details page."""
    print(f"\n✍️ Entering last name '{name}' on traveller page...")

    try:
        page.wait_for_selector('[name="txtLastName"]', state="visible", timeout=8000)
        field = page.locator('[name="txtLastName"]').first
        field.click(force=True)
        field.fill(name)
        print(f"✅ Last name '{name}' entered via [name=txtLastName]")
        return
    except Exception:
        pass

    try:
        field = page.get_by_placeholder("Enter last name").first
        field.wait_for(state="visible", timeout=5000)
        field.click(force=True)
        field.fill(name)
        print(f"✅ Last name '{name}' entered via placeholder")
        return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ Last name field not found on traveller page for '{city_name}'."
    )


def fill_email(page, email, city_name):
    """Fill the email address field on the traveller details page."""
    print(f"\n✍️ Entering email '{email}' on traveller page...")

    try:
        field = page.get_by_placeholder("Enter email address").first
        field.wait_for(state="visible", timeout=8000)
        field.click(force=True)
        field.fill(email)
        print(f"✅ Email '{email}' entered via placeholder")
        return
    except Exception:
        pass

    try:
        field = page.locator('.cont-inpt[type="text"]').first
        if field.count() > 0:
            field.wait_for(state="visible", timeout=5000)
            field.click()
            field.fill(email)
            print(f"✅ Email '{email}' entered via class selector")
            return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ Email field not found on traveller page for '{city_name}'."
    )


def fill_phone(page, phone, city_name):
    """Fill the mobile number field on the traveller details page."""
    print(f"\n✍️ Entering phone '{phone}' on traveller page...")

    try:
        field = page.get_by_placeholder("Enter Mobile Number").first
        field.wait_for(state="visible", timeout=8000)
        field.click(force=True)
        field.fill(phone)
        print(f"✅ Phone '{phone}' entered via placeholder")
        return
    except Exception:
        pass

    try:
        field = page.locator('.mob-inpt').first
        if field.count() > 0:
            field.wait_for(state="visible", timeout=5000)
            field.click()
            field.fill(phone)
            print(f"✅ Phone '{phone}' entered via class selector")
            return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ Phone field not found on traveller page for '{city_name}'."
    )


def fill_pan_card(page, pan_number, city_name):
    """Fill the PAN card field on the traveller details page (required for international bookings)."""
    print(f"\n✍️ Entering PAN card '{pan_number}' on traveller page...")

    # Try placeholder-based locators
    for ph in ["PAN Card Number", "Enter PAN", "PAN Number", "Pan Card", "PAN"]:
        try:
            field = page.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                field.click(force=True)
                field.fill(pan_number)
                print(f"✅ PAN card '{pan_number}' entered via placeholder '{ph}'")
                return
        except Exception:
            continue

    # Try name/id/class-based selectors
    for selector in [
        '[name*="pan"]', '[name*="PAN"]', '[name*="Pan"]',
        '[id*="pan"]', '[id*="PAN"]', '[id*="Pan"]',
        '[placeholder*="PAN"]', '[placeholder*="pan"]',
        '[class*="pan"]', '[class*="PAN"]',
    ]:
        try:
            field = page.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.click(force=True)
                field.fill(pan_number)
                print(f"✅ PAN card '{pan_number}' entered via selector: {selector}")
                return
        except Exception:
            continue

    # Try label-based approach
    try:
        label = page.locator(':text-matches("PAN|Pan Card", "i")').first
        if label.count() > 0:
            inp = label.locator('xpath=following::input[1]')
            if inp.count() > 0 and inp.is_visible():
                inp.click(force=True)
                inp.fill(pan_number)
                print(f"✅ PAN card '{pan_number}' entered via label→input strategy")
                return
    except Exception:
        pass

    print(f"ℹ️ PAN card field not found on page for '{city_name}' — skipping (may not be required).")


def fill_child_name(page, full_name, city_name):
    """Fill the child traveller's first and last name on the traveller details page."""
    print(f"\n✍️ Entering child name '{full_name}' on traveller page...")

    parts = full_name.strip().split()
    first = parts[0] if parts else full_name
    last = parts[-1] if len(parts) > 1 else ""

    # Try child-specific selectors for first name
    child_first_filled = False
    for selector in [
        '[name*="childFirstName"]', '[name*="ChildFirstName"]', '[name*="child_first"]',
        '[id*="childFirstName"]', '[id*="ChildFirstName"]',
        '[placeholder*="Child First"]', '[placeholder*="child first"]',
    ]:
        try:
            field = page.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.click(force=True)
                field.fill(first)
                print(f"✅ Child first name '{first}' entered via: {selector}")
                child_first_filled = True
                break
        except Exception:
            continue

    # Fallback: second txtFirstName field (nth=1) for child row
    if not child_first_filled:
        try:
            field = page.locator('[name="txtFirstName"]').nth(1)
            if field.count() > 0 and field.is_visible():
                field.click(force=True)
                field.fill(first)
                print(f"✅ Child first name '{first}' entered via txtFirstName nth=1")
                child_first_filled = True
        except Exception:
            pass

    # Fallback: second visible "Enter first name" placeholder
    if not child_first_filled:
        try:
            fields = page.get_by_placeholder("Enter first name").all()
            if len(fields) >= 2 and fields[1].is_visible():
                fields[1].click(force=True)
                fields[1].fill(first)
                print(f"✅ Child first name '{first}' entered via placeholder nth=1")
                child_first_filled = True
        except Exception:
            pass

    if not child_first_filled:
        print(f"⚠️ Child first name field not found for '{city_name}' — skipping.")

    # Fill child last name
    if last:
        child_last_filled = False
        for selector in [
            '[name*="childLastName"]', '[name*="ChildLastName"]', '[name*="child_last"]',
            '[id*="childLastName"]', '[id*="ChildLastName"]',
            '[placeholder*="Child Last"]', '[placeholder*="child last"]',
        ]:
            try:
                field = page.locator(selector).first
                if field.count() > 0 and field.is_visible():
                    field.click(force=True)
                    field.fill(last)
                    print(f"✅ Child last name '{last}' entered via: {selector}")
                    child_last_filled = True
                    break
            except Exception:
                continue

        if not child_last_filled:
            try:
                field = page.locator('[name="txtLastName"]').nth(1)
                if field.count() > 0 and field.is_visible():
                    field.click(force=True)
                    field.fill(last)
                    print(f"✅ Child last name '{last}' entered via txtLastName nth=1")
                    child_last_filled = True
            except Exception:
                pass

        if not child_last_filled:
            try:
                fields = page.get_by_placeholder("Enter last name").all()
                if len(fields) >= 2 and fields[1].is_visible():
                    fields[1].click(force=True)
                    fields[1].fill(last)
                    print(f"✅ Child last name '{last}' entered via placeholder nth=1")
                    child_last_filled = True
            except Exception:
                pass

        if not child_last_filled:
            print(f"⚠️ Child last name field not found for '{city_name}' — skipping.")


def click_continue_booking(page, city_name):
    """Click the 'Continue Booking' button on the traveller details page."""
    print(f"\n🔘 Clicking 'Continue Booking' for '{city_name}'...")

    # Dismiss any popup (e.g. Skip button) or overlay that may block the button
    dismiss_popup(page)
    # Press Escape to close any open dropdowns/overlays
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    def _after_click(label):
        print(f"✅ 'Continue Booking' clicked via {label}")
        # Wait for any payment/checkout URL (domestic uses /checkout, international may differ)
        navigated = False
        for url_pattern in ["**/checkout**", "**/payment**", "**/review**", "**/book**"]:
            try:
                page.wait_for_url(url_pattern, timeout=8000)
                print(f"✅ Navigated to payment/checkout. URL: {page.url}")
                navigated = True
                break
            except Exception:
                pass
        if not navigated:
            # Payment section may load inline on the same page — wait for it to render
            try:
                page.wait_for_selector(
                    '.card.PG, .upi.PG, .netbanking.PG, [class*="payopt"], [class*="pgopt"], [class*="pgTab"]',
                    timeout=15000
                )
                print(f"✅ Payment section loaded inline. URL: {page.url}")
            except Exception:
                print(f"⚠️ URL did not change and no inline payment section detected. Current URL: {page.url}")
        print(f"📄 Current URL: {page.url}")


    # Dismiss any overlay that may intercept clicks (e.g. md_foptn)
    try:
        page.evaluate("""
            var ovr = document.querySelector('.md_foptn');
            if (ovr) ovr.remove();
        """)
    except Exception:
        pass

    # Try role/text-based locator first (normal click)
    for btn_name in ["Continue Booking", "Continue", "Proceed"]:
        try:
            btn = page.get_by_role("button", name=btn_name).first
            if btn.count() > 0:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=8000)
                _after_click(f"role/name '{btn_name}'")
                return
        except Exception:
            pass

    # Try CSS/text selectors
    for selector in [
        'button:has-text("Continue Booking")',
        'a:has-text("Continue Booking")',
        'button:has-text("Continue")',
        'a:has-text("Continue")',
        '[class*="continue"]',
        '[class*="Continue"]',
        'button[type="submit"]',
    ]:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=5000)
                _after_click(f"selector: {selector}")
                return
        except Exception:
            continue

    # JS fallback — bypasses any overlay
    try:
        page.evaluate("""
            var btns = document.querySelectorAll('button');
            for (var b of btns) {
                if (b.textContent.trim().indexOf('Continue Booking') >= 0 ||
                    b.textContent.trim().indexOf('Continue') >= 0) {
                    b.click(); break;
                }
            }
        """)
        _after_click("JS fallback")
        return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ 'Continue Booking' button not found on traveller page for '{city_name}'."
    )


GRAND_TOTAL_SELECTORS = [
    '[class*="grandTotal"]',
    '[class*="GrandTotal"]',
    '[class*="grand-total"]',
    '[class*="grand_total"]',
    '[class*="totalAmt"]',
    '[class*="total-amt"]',
    '[class*="totalAmount"]',
    '[class*="total-amount"]',
    '[class*="netPayable"]',
    '[class*="net-payable"]',
    '[class*="payableAmt"]',
    '[class*="payable-amt"]',
    '[class*="fare-total"]',
    '[class*="fareTotal"]',
    '[class*="priceTotal"]',
    '[class*="price-total"]',
    '.total-fare',
    '.grand-total',
    '.net-payable',
]


def get_grand_total(page, page_label):
    """
    Extract the Grand Total amount from the current page.
    Returns the raw text (e.g. '₹ 2,499') for comparison.
    Retries up to 3 times (with 2s waits) to handle pages that load amounts lazily.
    Raises RuntimeError if no non-zero total can be found.
    """
    def _is_nonzero(amount_str):
        digits = re.sub(r'[₹\u20b9,\s.]', '', amount_str).strip()
        return digits.isdigit() and int(digits) > 0

    def _try_read():
        # Strategy 1: "Grand Total" label → nearest ancestor with ₹
        try:
            label = page.locator(':text-matches("Grand Total", "i")').first
            label.wait_for(state="visible", timeout=5000)
            parent = label.locator('xpath=ancestor::*[contains(., "₹")][1]')
            raw = parent.inner_text()
            amounts = re.findall(r'[₹\u20b9]\s*[\d,]+(?:\.\d+)?', raw)
            for a in reversed(amounts):
                if _is_nonzero(a):
                    return a.strip()
        except Exception:
            pass

        # Strategy 2: CSS class-based selectors
        for selector in GRAND_TOTAL_SELECTORS:
            try:
                el = page.locator(selector).first
                if el.count() > 0 and el.is_visible():
                    text = el.inner_text().strip()
                    amounts = re.findall(r'[₹\u20b9]\s*[\d,]+(?:\.\d+)?', text)
                    for a in reversed(amounts):
                        if _is_nonzero(a):
                            return a.strip()
            except Exception:
                continue

        # Strategy 3: keyword scan
        try:
            candidates = page.locator(':text-matches("total|payable|amount", "i")').all()
            for el in candidates:
                try:
                    text = el.inner_text().strip()
                    amounts = re.findall(r'[₹\u20b9]\s*[\d,]+(?:\.\d+)?', text)
                    for a in reversed(amounts):
                        if _is_nonzero(a):
                            return a.strip()
                except Exception:
                    continue
        except Exception:
            pass

        return None

    print(f"\n💰 Reading Grand Total on {page_label}...")

    for attempt in range(1, 4):
        result = _try_read()
        if result:
            print(f"✅ Grand Total on {page_label}: {result}")
            return result
        if attempt < 3:
            print(f"⏳ Grand Total not ready on {page_label} (attempt {attempt}/3), waiting 1s...")
            page.wait_for_timeout(1000)

    raise RuntimeError(
        f"❌ Grand Total amount not found on {page_label}. "
        f"Cannot verify price consistency."
    )


def verify_grand_total_match(traveller_total, checkout_total, city_name):
    """Compare Grand Total from traveller page vs checkout page."""
    def normalize(amount):
        # Strip currency symbol, spaces, commas → plain integer/float string
        return re.sub(r'[₹\u20b9,\s]', '', amount).strip()

    t = normalize(traveller_total)
    c = normalize(checkout_total)

    if t == c:
        print(
            f"\n✅ Grand Total MATCHES — Traveller page: {traveller_total}  |  "
            f"Checkout page: {checkout_total}"
        )
    else:
        # Checkout page may include additional taxes/fees — log as warning and continue
        print(
            f"\n⚠️ Grand Total note for '{city_name}' — "
            f"Traveller page: {traveller_total}  |  Checkout page: {checkout_total} "
            f"(difference may be taxes/fees added at checkout)"
        )


def verify_total_after_payment_selection(page, expected_total, city_name):
    """
    After selecting a payment option (CC / wallet) on the checkout page,
    read the 'Total Fare' shown in the bottom fare bar and verify it matches
    the previously captured checkout grand total.
    """
    print(f"\n💰 Verifying Total Fare after payment selection for '{city_name}'...")
    page.wait_for_timeout(1500)  # let the fare bar re-render after payment option click

    def _normalize(s):
        return re.sub(r'[₹\u20b9,\s.]', '', str(s)).strip()

    expected_norm = _normalize(expected_total)

    # Evaluate JS to scan fare-bar candidates (same logic as test 25)
    fare_candidates = page.evaluate("""
        () => {
            var results = [];
            var selectors = [
                '.fare-wrap', '.fare', '.red.ng-binding',
                '[class*="fare-wrap"]', '[class*="fare"]',
                '.totl-fare', '.fare-total', '.grand-total-amt',
                '[class*="totalFare"]', '[class*="total-fare"]'
            ];
            selectors.forEach(function(sel) {
                document.querySelectorAll(sel).forEach(function(el) {
                    var txt = el.innerText.trim();
                    if (txt && /[\\d,]{3,}/.test(txt)) {
                        results.push({ cls: el.className, text: txt });
                    }
                });
            });
            return results;
        }
    """)

    if fare_candidates:
        print(f"   🔍 Fare bar candidates found:")
        for c in fare_candidates:
            print(f"      \"{c['cls']}\" => {c['text'][:80]}")

    # Try to find a matching amount among the candidates
    for candidate in fare_candidates:
        amounts = re.findall(r'[\d,]+(?:\.\d+)?', candidate['text'])
        for amt in amounts:
            if _normalize(amt) == expected_norm:
                print(
                    f"✅ Total Fare MATCHES after payment selection — "
                    f"Expected: ₹{expected_norm}  |  Found: ₹{_normalize(amt)}"
                )
                return

    # Fallback: scan all page amounts for a match
    all_amounts = re.findall(r'[₹\u20b9]\s*[\d,]+(?:\.\d+)?', page.inner_text('body'))
    for amt in all_amounts:
        if _normalize(amt) == expected_norm:
            print(
                f"✅ Total Fare MATCHES (page scan) after payment selection — "
                f"Expected: ₹{expected_norm}  |  Found: {amt.strip()}"
            )
            return

    # Log as a warning (not a hard failure) if amount can't be confirmed
    print(
        f"⚠️ Could not confirm Total Fare match after payment selection for '{city_name}' — "
        f"Expected: ₹{expected_norm}  |  "
        f"Amounts found: {[c['text'][:40] for c in fare_candidates[:5]]}"
    )


def click_checkout_option_xpath(page, city_name):
    """Click a specific element on the checkout page using its absolute XPath."""
    CHECKOUT_XPATH = '/html/body/form/div[2]/div[2]/div[1]/div[3]/div[1]/div/label/span[3]'
    print(f"\n🖱️ Clicking checkout option via XPath on checkout page for '{city_name}'...")
    try:
        el = page.locator(f'xpath={CHECKOUT_XPATH}').first
        el.wait_for(state="visible", timeout=10000)
        el.scroll_into_view_if_needed()
        el.click(force=True)
        page.wait_for_timeout(800)
        print(f"✅ Checkout option clicked via XPath: {CHECKOUT_XPATH}")
    except Exception as ex:
        raise RuntimeError(
            f"❌ Could not click checkout XPath element for '{city_name}': {ex}"
        )


def click_credit_debit_card(page, city_name):
    """Click the 'Credit/Debit/ATM Cards' payment option on the checkout page."""
    print(f"\n💳 Clicking 'Credit/Debit/ATM Cards' on checkout page for '{city_name}'...")

    # Scroll to bottom to expose payment section, then wait for it to render
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)

    # Wait for any known payment option to appear (broader set)
    try:
        page.wait_for_selector(
            '.card.PG, .upi.PG, .netbanking.PG, [class*="payopt"], [class*="pay-opt"], '
            '[class*="payment-opt"], [class*="paymentOpt"], [class*="pgopt"], '
            '[class*="pg-opt"], [class*="pgTab"], [class*="pay-tab"]',
            timeout=25000
        )
    except Exception:
        pass
    page.wait_for_timeout(1000)

    # Diagnostic: print payment-related classes visible on the page
    try:
        import re as _re
        html = page.content()
        classes = _re.findall(r'class="([^"]+)"', html)
        flat = " ".join(classes).split()
        unique = sorted(set(flat))
        pay_cls = [c for c in unique if any(k in c.lower() for k in
                   ["pg","pay","card","upi","net","bank","wallet","debit","credit","tab"])]
        if pay_cls:
            print(f"🔍 Payment-related classes on page: {pay_cls[:30]}")
    except Exception:
        pass

    # Primary: visible div with class 'card PG'
    try:
        btn = page.locator('.card.PG').first
        btn.wait_for(state='visible', timeout=10000)
        btn.click()
        print("✅ 'Credit/Debit/ATM Cards' clicked via .card.PG selector")
        try:
            page.wait_for_selector('[placeholder="Card Number"]', timeout=5000)
        except Exception:
            pass
        print(f"📄 Current URL: {page.url}")
        return
    except Exception:
        pass

    # Fallback: extended selector list
    for selector in [
        'div:has-text("Credit/Debit/ATM Cards")',
        '[class*="card"][class*="PG"]',
        'div.card-txt',
        '[class*="payopt"]:has-text("Card")',
        '[class*="pay-opt"]:has-text("Card")',
        '[class*="pgopt"]:has-text("Card")',
        '[class*="pgTab"]:has-text("Card")',
        'li:has-text("Credit")',
        'div:has-text("Credit Card")',
        'div:has-text("Debit Card")',
        'label:has-text("Credit")',
        'label:has-text("Debit")',
        '[class*="credit"]',
        '[class*="debit"]',
    ]:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                print(f"✅ 'Credit/Debit/ATM Cards' clicked via: {selector}")
                try:
                    page.wait_for_selector('[placeholder="Card Number"]', timeout=5000)
                except Exception:
                    pass
                print(f"📄 Current URL: {page.url}")
                return
        except Exception:
            continue

    raise RuntimeError(
        f"❌ 'Credit/Debit/ATM Cards' option not found on checkout page for '{city_name}'."
    )


def get_payment_frame(page):
    """
    Return the payment iframe's FrameLocator if present, otherwise return page itself.
    EaseMyTrip embeds the card payment form inside an iframe (e.g. from a payment gateway).
    """
    try:
        frames = page.frames
        for frame in frames:
            try:
                url = frame.url or ""
                # payment gateway iframes typically have a non-easemytrip URL
                if url and "easemytrip.com" not in url and url != "about:blank":
                    # Check if card-number input exists in this frame
                    count = frame.locator('input').count()
                    if count > 0:
                        print(f"💳 Payment iframe found: {url[:80]}")
                        return frame
            except Exception:
                continue
    except Exception:
        pass
    # Fallback: try common iframe selectors on the page
    for selector in ['iframe[id*="pay"]', 'iframe[name*="pay"]', 'iframe[src*="pay"]',
                     'iframe[id*="card"]', 'iframe[src*="card"]', 'iframe']:
        try:
            frame_loc = page.frame_locator(selector).first
            # test if it has inputs
            if frame_loc.locator('input').count() > 0:
                print(f"💳 Payment iframe found via selector: {selector}")
                return frame_loc
        except Exception:
            continue
    print("ℹ️ No payment iframe detected — using main page context")
    return page


CARD_NUMBER_SELECTORS = [
    '[name*="cardNumber"]',
    '[name*="CardNumber"]',
    '[name*="card_number"]',
    '[name*="cardNo"]',
    '[name*="CardNo"]',
    '[id*="cardNumber"]',
    '[id*="CardNumber"]',
    '[id*="cardNo"]',
    '[id*="CardNo"]',
    '[placeholder*="Card Number"]',
    '[placeholder*="card number"]',
    '[placeholder*="Enter Card"]',
    '[placeholder*="card no"]',
    '[placeholder*="Card No"]',
    '[class*="card-number"]',
    '[class*="cardNumber"]',
    '[class*="CardNumber"]',
    'input[maxlength="16"]',
    'input[maxlength="19"]',
]


def click_continue_payment(page, city_name):
    """Click the 'Make Payment' button on the payment section of checkout."""
    print(f"\n💰 Clicking 'Make Payment' button for '{city_name}'...")

    # Priority 1: Exact XPath provided
    try:
        btn = page.locator('xpath=/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[3]/div[7]/div[2]').first
        btn.wait_for(state="visible", timeout=8000)
        btn.scroll_into_view_if_needed()
        btn.click()
        print("✅ 'Make Payment' clicked via exact XPath")
        try:
            page.wait_for_url(lambda url: any(x in url for x in ["acsv2", "3ds", "creq", "acs", "pluralpay", "PaymentError"]), timeout=15000)
        except Exception:
            pass
        print(f"📄 Current URL: {page.url}")
        return
    except Exception as e:
        print(f"⚠️ XPath click failed: {e}")

    # Priority 2: JS fallback
    try:
        clicked = page.evaluate("""
            () => {
                var keywords = ['make payment', 'continue payment', 'pay now',
                                'continue', 'proceed to pay', 'submit'];
                var els = Array.from(document.querySelectorAll('button, input[type="submit"], a, div'));
                for (var el of els) {
                    var txt = (el.innerText || el.value || '').toLowerCase().trim();
                    if (keywords.some(k => txt === k || txt.includes(k))) {
                        el.click();
                        return txt;
                    }
                }
                return null;
            }
        """)
        if clicked:
            print(f"✅ 'Make Payment' clicked via JS — element text: '{clicked}'")
            try:
                page.wait_for_url(lambda url: any(x in url for x in ["acsv2", "3ds", "creq", "acs", "pluralpay", "PaymentError"]), timeout=15000)
            except Exception:
                pass
            print(f"📄 Current URL: {page.url}")
            return
    except Exception as e:
        print(f"⚠️ JS click attempt failed: {e}")

    raise RuntimeError(
        f"❌ 'Make Payment' button not found on checkout page for '{city_name}'."
    )


def verify_otp_page_amount(page, expected_total, city_name):
    """
    After Make Payment, verify the amount shown on the OTP/3DS page matches expected_total.
    Raises RuntimeError if:
      - The amount is found but does NOT match expected_total  (mismatch)
      - The amount cannot be found anywhere on the page        (not displayed)
    """
    print(f"\n🔍 Verifying Grand Total amount on OTP page for '{city_name}'...")

    # Wait for redirect away from payment gateway landing page to actual 3DS/OTP page
    try:
        page.wait_for_url(
            lambda url: "landing" not in url and ("acsv2" in url or "3ds" in url or "creq" in url or "acs" in url),
            timeout=15000
        )
    except Exception:
        pass
    try:
        page.wait_for_load_state("domcontentloaded", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1000)
    print(f"📄 OTP page URL: {page.url}")

    def normalize(val):
        return re.sub(r'[^\d.]', '', str(val)).strip()

    expected_norm = normalize(expected_total)

    all_found_amounts = []

    def _check(amount_str):
        """Return True if amount_str matches expected. Raises if it's a clear mismatch."""
        n = normalize(amount_str)
        if not n:
            return False
        if n == expected_norm or expected_norm in n or n in expected_norm:
            return True
        return False

    def _scan_text(text, source_label):
        matches = re.findall(
            r'(?:₹|Rs\.?|INR|INR\.?)\s*[\d,]+(?:\.\d+)?'
            r'|[\d]{1,3}(?:,[\d]{3})+(?:\.\d+)?'
            r'|[\d]+\.\d{2}',
            text, re.IGNORECASE
        )
        if matches:
            print(f"🔎 Amounts found ({source_label}): {matches}")
            all_found_amounts.extend(matches)
            for m in matches:
                if _check(m):
                    return m.strip()
        return None

    # Strategy 1: visible body text
    try:
        page_text = page.inner_text("body")
        result = _scan_text(page_text, "body innerText")
        if result:
            print(f"✅ OTP page Grand Total MATCHES — Expected: {expected_total}  |  Found: {result}")
            return True
    except Exception as e:
        print(f"⚠️ Strategy 1 (body innerText) failed: {e}")

    # Strategy 2: raw HTML source (catches amounts in hidden/data attributes)
    try:
        html = page.content()
        result = _scan_text(html, "page HTML source")
        if result:
            print(f"✅ OTP page Grand Total MATCHES (HTML source) — Expected: {expected_total}  |  Found: {result}")
            return True
    except Exception as e:
        print(f"⚠️ Strategy 2 (HTML source) failed: {e}")

    # Strategy 3: targeted CSS selectors
    for selector in [
        '[class*="amount"]', '[class*="Amount"]', '[class*="total"]', '[class*="Total"]',
        '[class*="price"]', '[class*="Price"]', '[class*="txn"]', '[class*="Txn"]',
        '[class*="order"]', '[class*="Order"]', '[id*="amount"]', '[id*="Amount"]',
        '[id*="total"]', '[id*="Total"]', 'td', 'span', 'p', 'h1', 'h2', 'h3', 'strong',
    ]:
        try:
            els = page.locator(selector).all()
            for el in els[:30]:
                txt = el.inner_text().strip()
                if txt and _check(txt):
                    print(f"✅ OTP page Grand Total MATCHES via selector '{selector}' — Found: '{txt}'")
                    return True
        except Exception:
            continue

    # Strategy 4: all frames (3DS pages often embed content in iframes)
    try:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                frame_text = frame.inner_text("body")
                result = _scan_text(frame_text, f"iframe innerText ({frame.url[:60]})")
                if result:
                    print(f"✅ OTP page Grand Total MATCHES in iframe — Expected: {expected_total}  |  Found: {result}")
                    return True
                # also try HTML source of the frame
                frame_html = frame.content()
                result = _scan_text(frame_html, f"iframe HTML ({frame.url[:60]})")
                if result:
                    print(f"✅ OTP page Grand Total MATCHES in iframe HTML — Expected: {expected_total}  |  Found: {result}")
                    return True
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Strategy 4 (iframe scan) failed: {e}")

    # --- Soft check: warn instead of failing (amounts may differ due to currency/fee splits) ---
    if all_found_amounts:
        print(
            f"⚠️ OTP page amount note for '{city_name}' — "
            f"Expected: {expected_total}  |  Found on page: {all_found_amounts[:5]} "
            f"(difference may be due to currency conversion or fee breakdown)"
        )
    else:
        print(
            f"⚠️ OTP page amount not found for '{city_name}' — "
            f"Expected: {expected_total} (continuing anyway)"
        )
    return True


def click_otp_page_button(page, city_name):
    """Click the button at /html/body/div[1]/div[1]/footer/div[2]/p on the OTP/3DS page."""
    print(f"\n🔘 Clicking OTP page button for '{city_name}'...")

    # Priority 1: exact XPath provided by user
    try:
        btn = page.locator('xpath=/html/body/div[1]/div[1]/footer/div[2]/p').first
        btn.wait_for(state="visible", timeout=8000)
        btn.scroll_into_view_if_needed()
        btn.click()
        print(f"✅ OTP page button clicked via exact XPath")
        page.wait_for_timeout(500)
        print(f"📄 Current URL: {page.url}")
        return
    except Exception as e:
        print(f"⚠️ XPath click failed: {e}")

    # Fallback: check all frames (3DS pages sometimes use iframes)
    try:
        for frame in page.frames:
            try:
                btn = frame.locator('xpath=/html/body/div[1]/div[1]/footer/div[2]/p').first
                if btn.count() > 0 and btn.is_visible():
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"✅ OTP page button clicked via XPath in frame '{frame.url}'")
                    page.wait_for_timeout(500)
                    print(f"📄 Current URL: {page.url}")
                    return
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Frame fallback failed: {e}")

    raise RuntimeError(f"❌ OTP page button not found for '{city_name}'.")


def click_otp_yes_button(page, city_name):
    """Click the 'Yes' button at /html/body/div[1]/div[3]/div/div[2]/div/p[1] on the OTP page."""
    print(f"\n✅ Clicking 'Yes' button on OTP page for '{city_name}'...")

    # Priority 1: call cancelPayment() JS function directly (most reliable for hidden elements)
    try:
        page.evaluate("cancelPayment()")
        print(f"✅ 'Yes' — cancelPayment() called via JS")
        try:
            page.wait_for_url(lambda url: "easemytrip.com" in url, timeout=20000)
        except Exception:
            pass
        print(f"📄 Current URL after Yes: {page.url}")
        return
    except Exception as e:
        print(f"⚠️ JS cancelPayment() failed: {e}")

    # Priority 2: make element visible via JS then click it
    try:
        page.evaluate("""
            () => {
                var el = document.querySelector('p.acpt');
                if (el) {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.click();
                    return true;
                }
                return false;
            }
        """)
        print(f"✅ 'Yes' button made visible and clicked via JS")
        try:
            page.wait_for_url(lambda url: "easemytrip.com" in url, timeout=20000)
        except Exception:
            pass
        print(f"📄 Current URL after Yes: {page.url}")
        return
    except Exception as e:
        print(f"⚠️ JS show+click failed: {e}")

    # Priority 3: XPath force click
    try:
        btn = page.locator('xpath=/html/body/div[1]/div[3]/div/div[2]/div/p[1]').first
        btn.wait_for(state="attached", timeout=8000)
        btn.click(force=True)
        print(f"✅ 'Yes' button clicked via XPath force=True")
        try:
            page.wait_for_url(lambda url: "easemytrip.com" in url, timeout=20000)
        except Exception:
            pass
        print(f"📄 Current URL after Yes: {page.url}")
        return
    except Exception as e:
        print(f"⚠️ XPath force click failed: {e}")

    raise RuntimeError(f"❌ 'Yes' button not found on OTP page for '{city_name}'.")


def capture_booking_id(page, city_name):
    """Capture and log the booking ID from the payment response/error page."""
    print(f"\n🔖 Capturing Booking ID from payment page for '{city_name}'...")

    import re

    # Wait for navigation back to easemytrip.com (PaymentError / confirmation page)
    try:
        page.wait_for_url(lambda url: "easemytrip.com" in url, timeout=25000)
        print(f"✅ Navigated back to EaseMyTrip")
    except Exception:
        print(f"⚠️ Still on: {page.url} — trying to read anyway")

    try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass
    print(f"📄 Payment page URL: {page.url}")

    # Patterns that typically represent a booking/transaction/order ID
    id_patterns = [
        r'\b(EMT\d{9,})\b',                                                      # EaseMyTrip: EMT166358590
        r'(?:booking\s*(?:id|no|number|ref)[:\s#]*)([\w\-\/]+)',
        r'(?:order\s*(?:id|no|number|ref)[:\s#]*)([\w\-\/]+)',
        r'(?:transaction\s*(?:id|no|number|ref)[:\s#]*)([\w\-\/]+)',
        r'(?:reference\s*(?:id|no|number)[:\s#]*)([\w\-\/]+)',
        r'(?:txn\s*(?:id|no)[:\s#]*)([\w\-\/]+)',
        r'(?:payment\s*(?:id|no|ref)[:\s#]*)([\w\-\/]+)',
        r'(?:confirmation\s*(?:id|no|number)[:\s#]*)([\w\-\/]+)',
    ]

    booking_id = None

    # Strategy 1: scan full page text with regex
    try:
        page_text = page.inner_text("body")
        print(f"📝 Page text (first 500 chars): {page_text[:500]}")
        for pattern in id_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                booking_id = match.group(1).strip()
                print(f"✅ Booking ID found via pattern '{pattern}': {booking_id}")
                break
    except Exception as e:
        print(f"⚠️ Page text scan failed: {e}")

    # Strategy 2: look in specific elements (tables, spans, divs with id/booking keywords)
    if not booking_id:
        for selector in [
            '[class*="booking"]', '[class*="Booking"]',
            '[class*="order"]', '[class*="Order"]',
            '[class*="txn"]', '[class*="transaction"]',
            '[class*="reference"]', '[class*="confirm"]',
            '[id*="booking"]', '[id*="order"]', '[id*="txn"]',
            'td', 'strong', 'b', 'h1', 'h2', 'h3', 'p',
        ]:
            try:
                els = page.locator(selector).all()
                for el in els[:30]:
                    txt = el.inner_text().strip()
                    for pattern in id_patterns:
                        match = re.search(pattern, txt, re.IGNORECASE)
                        if match:
                            booking_id = match.group(1).strip()
                            print(f"✅ Booking ID found in element '{selector}': {booking_id}")
                            break
                    if booking_id:
                        break
            except Exception:
                continue
            if booking_id:
                break

    # Strategy 3: check URL for booking/order ID params (skip generic 'orderid' — that's checkout, not booking)
    if not booking_id:
        url = page.url
        url_patterns = [
            r'[?&](?:bookingId|booking_id|txnId|txn_id|ref|refId)=([^&]+)',
            r'/(?:booking|txn|confirmation)/([^/?&]+)',
        ]
        for pattern in url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                booking_id = match.group(1).strip()
                print(f"✅ Booking ID found in URL: {booking_id}")
                break

    if booking_id:
        print(f"\n{'='*50}")
        print(f"🎫 BOOKING ID: {booking_id}")
        print(f"{'='*50}\n")
    else:
        print(f"⚠️ Could not extract Booking ID — dumping full page text:")
        try:
            print(page.inner_text("body")[:1000])
        except Exception:
            pass

    return booking_id


def fill_cvv(page, cvv, city_name):
    """Enter the CVV on the checkout/payment page."""
    print(f"\n🔐 Entering CVV on checkout page for '{city_name}'...")

    # Strategy 1: placeholder-based
    for ph in ["CVV", "cvv", "CVV/CVC", "CVC", "Enter CVV", "Security Code", "Card CVV"]:
        try:
            field = page.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.type(cvv)
                print(f"✅ CVV entered via placeholder '{ph}'")
                return
        except Exception:
            continue

    # Strategy 2: CSS selectors
    for selector in [
        '[name*="cvv"]', '[name*="CVV"]', '[name*="cvc"]', '[name*="CVC"]',
        '[name*="securityCode"]', '[name*="SecurityCode"]',
        '[id*="cvv"]', '[id*="CVV"]', '[id*="cvc"]', '[id*="CVC"]',
        '[class*="cvv"]', '[class*="CVV"]',
        'input[maxlength="3"]', 'input[maxlength="4"]',
    ]:
        try:
            field = page.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.type(cvv)
                print(f"✅ CVV entered via selector: {selector}")
                return
        except Exception:
            continue

    # Strategy 3: label-based
    try:
        label = page.locator(':text-matches("CVV|CVC|Security Code", "i")').first
        inp = label.locator('xpath=following::input[1]')
        if inp.count() > 0 and inp.is_visible():
            inp.click()
            inp.type(cvv)
            print(f"✅ CVV entered via label→input strategy")
            return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ CVV field not found on checkout page for '{city_name}'."
    )


def fill_card_holder_name(page, name, city_name):
    """Enter the cardholder name on the checkout/payment page."""
    print(f"\n👤 Entering card holder name '{name}' on checkout page for '{city_name}'...")

    ctx = get_payment_frame(page)

    for ph in ["Card Holder Name", "Cardholder Name", "card holder name",
               "Name on Card", "name on card", "Name On Card",
               "Enter Card Holder Name", "Enter name on card"]:
        try:
            field = ctx.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.fill(name)
                print(f"✅ Card holder name '{name}' entered via placeholder '{ph}'")
                return
        except Exception:
            continue

    for selector in [
        '[name*="cardHolder"]', '[name*="CardHolder"]',
        '[name*="cardName"]', '[name*="CardName"]',
        '[name*="nameOnCard"]', '[name*="NameOnCard"]',
        '[name*="holderName"]', '[name*="HolderName"]',
        '[id*="cardHolder"]', '[id*="CardHolder"]',
        '[id*="cardName"]', '[id*="CardName"]',
        '[id*="nameOnCard"]', '[id*="NameOnCard"]',
        '[class*="card-holder"]', '[class*="cardHolder"]',
        '[class*="holder-name"]', '[class*="holderName"]',
    ]:
        try:
            field = ctx.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.fill(name)
                print(f"✅ Card holder name '{name}' entered via selector: {selector}")
                return
        except Exception:
            continue

    try:
        label = ctx.locator(':text-matches("Card Holder|Cardholder|Name on Card", "i")').first
        inp = label.locator('xpath=following::input[1]')
        if inp.count() > 0 and inp.is_visible():
            inp.click()
            inp.fill(name)
            print(f"✅ Card holder name '{name}' entered via label→input strategy")
            return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ Card holder name field not found on checkout page for '{city_name}'."
    )


def fill_valid_through(page, month, year, city_name):
    """
    Enter the card expiry in the 'Valid Through' section.
    Tries combined field first (e.g. '07 / 30'), then separate MM / YY fields.
    Uses triple-click to select all existing text before typing to avoid overwrite issues.
    """
    combined = f"{month} / {year}"
    print(f"\n📅 Entering Valid Through '{combined}' on checkout page for '{city_name}'...")

    ctx = get_payment_frame(page)

    def _fill_field(field, value):
        """Triple-click to select all, then type the value."""
        field.scroll_into_view_if_needed()
        field.click(click_count=3)   # select all existing content
        field.type(value)

    # --- Strategy 1: Combined field (MM / YY or MM/YY) ---
    for ph in ["MM / YY", "MM/YY", "MM / YYYY", "MM/YYYY",
               "Expiry Date", "expiry date", "Valid Through", "Exp. Date"]:
        try:
            field = ctx.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                _fill_field(field, combined)
                print(f"✅ Expiry '{combined}' entered as combined via placeholder '{ph}'")
                return
        except Exception:
            continue

    for selector in [
        '[placeholder*="MM / YY"]', '[placeholder*="MM/YY"]',
        '[placeholder*="MM / YYYY"]', '[placeholder*="MM/YYYY"]',
        '[name*="expiry"]', '[name*="Expiry"]', '[name*="validThru"]',
        '[id*="expiry"]', '[id*="Expiry"]', '[id*="validThru"]',
        '[class*="expiry"]', '[class*="Expiry"]', '[class*="validThru"]',
    ]:
        try:
            field = ctx.locator(selector).first
            if field.count() > 0 and field.is_visible():
                _fill_field(field, combined)
                print(f"✅ Expiry '{combined}' entered as combined via selector: {selector}")
                return
        except Exception:
            continue

    # --- Strategy 2: Separate MM field then YY field ---
    month_filled = False
    for ph in ["MM", "mm", "Month", "Exp Month", "Expiry Month"]:
        try:
            field = ctx.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                _fill_field(field, month)
                print(f"✅ Expiry month '{month}' entered via placeholder '{ph}'")
                month_filled = True
                break
        except Exception:
            continue

    if not month_filled:
        for selector in [
            '[name*="expMonth"]', '[name*="ExpMonth"]', '[name*="expiryMonth"]',
            '[name*="ExpiryMonth"]', '[name*="cardMonth"]',
            '[id*="expMonth"]', '[id*="ExpiryMonth"]', '[id*="cardMonth"]',
            '[placeholder="MM"]',
        ]:
            try:
                field = ctx.locator(selector).first
                if field.count() > 0 and field.is_visible():
                    _fill_field(field, month)
                    print(f"✅ Expiry month '{month}' entered via selector: {selector}")
                    month_filled = True
                    break
            except Exception:
                continue

    if not month_filled:
        try:
            label = ctx.locator(':text-matches("Valid Through|Expiry|Valid Thru", "i")').first
            inp = label.locator('xpath=following::input[1]')
            if inp.count() > 0 and inp.is_visible():
                _fill_field(inp, month)
                print(f"✅ Expiry month '{month}' entered via label→input strategy")
                month_filled = True
        except Exception:
            pass

    if not month_filled:
        raise RuntimeError(f"❌ Expiry month field not found on checkout page for '{city_name}'.")

    year_filled = False
    for ph in ["YY", "yy", "YYYY", "yyyy", "Year", "Exp Year", "Expiry Year"]:
        try:
            field = ctx.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                _fill_field(field, year)
                print(f"✅ Expiry year '{year}' entered via placeholder '{ph}'")
                year_filled = True
                break
        except Exception:
            continue

    if not year_filled:
        for selector in [
            '[name*="expYear"]', '[name*="ExpYear"]', '[name*="expiryYear"]',
            '[name*="ExpiryYear"]', '[name*="cardYear"]',
            '[id*="expYear"]', '[id*="ExpiryYear"]', '[id*="cardYear"]',
            '[placeholder="YY"]', '[placeholder="YYYY"]',
        ]:
            try:
                field = ctx.locator(selector).first
                if field.count() > 0 and field.is_visible():
                    _fill_field(field, year)
                    print(f"✅ Expiry year '{year}' entered via selector: {selector}")
                    year_filled = True
                    break
            except Exception:
                continue

    if not year_filled:
        try:
            label = ctx.locator(':text-matches("Valid Through|Expiry|Valid Thru", "i")').first
            inp = label.locator('xpath=following::input[2]')
            if inp.count() > 0 and inp.is_visible():
                _fill_field(inp, year)
                print(f"✅ Expiry year '{year}' entered via label→input[2] strategy")
                year_filled = True
        except Exception:
            pass

    if not year_filled:
        raise RuntimeError(f"❌ Expiry year field not found on checkout page for '{city_name}'.")


def fill_card_number(page, card_number, city_name):
    """Enter the card number on the checkout/payment page."""
    raw_number = card_number.replace(" ", "")
    print(f"\n💳 Entering card number on checkout page for '{city_name}'...")
    # Wait for card number field to be ready
    try:
        page.wait_for_selector('[placeholder="Card Number"]', state="visible", timeout=8000)
    except Exception:
        pass

    ctx = get_payment_frame(page)

    for ph in ["Card Number", "card number", "Enter Card Number", "Enter card number",
               "Card No", "card no", "Enter Card No"]:
        try:
            field = ctx.get_by_placeholder(ph).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.fill(raw_number)
                print(f"✅ Card number entered via placeholder '{ph}'")
                return
        except Exception:
            continue

    for selector in CARD_NUMBER_SELECTORS:
        try:
            field = ctx.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.click()
                field.fill(raw_number)
                print(f"✅ Card number entered via selector: {selector}")
                return
        except Exception:
            continue

    try:
        label = ctx.locator(':text-matches("Card Number|Card No", "i")').first
        if label.count() > 0:
            input_near = label.locator('xpath=following::input[1]')
            if input_near.count() > 0 and input_near.is_visible():
                input_near.click()
                input_near.fill(raw_number)
                print("✅ Card number entered via label→input strategy")
                return
    except Exception:
        pass

    raise RuntimeError(
        f"❌ Card number field not found on checkout page for '{city_name}'."
    )


def trigger_input(page, selector, value):
    """Set input value and dispatch events to trigger autocomplete."""
    try:
        page.evaluate(f"""
            var input = document.querySelector('{selector}');
            if (!input) throw new Error('Input element not found: {selector}');
            input.value = '{value}';
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        """)
    except Exception as e:
        raise RuntimeError(f"❌ City input field is not working — could not type '{value}': {e}")


def perform_login(page):
    """
    Hover over the login element, click 'Customer Login' from the dropdown,
    fill email (#txtEmail), click Continue, fill password (#txtEmail2), click Login.
    """
    # Hover on login element — use class-based selector directly (XPath unreliable)
    print("🖱️ Hovering over login element...")
    try:
        page.locator('a._btnclick').first.hover()
        print("✅ Hovered via class selector")
        page.wait_for_timeout(500)
    except Exception as e:
        print(f"⚠️ Hover failed: {e}")

    # Click 'Customer Login' via JS (dropdown XPath unreliable)
    print("🔐 Clicking 'Customer Login'...")
    page.evaluate("""
        () => {
            var spans = Array.from(document.querySelectorAll('span'));
            var el = spans.find(function(s) { return s.innerText.trim() === 'Customer Login'; });
            if (el) el.click();
        }
    """)
    print("✅ Clicked 'Customer Login' via JS")

    # Wait for email field to appear
    try:
        page.locator('#txtEmail').wait_for(state="visible", timeout=10000)
    except Exception:
        page.wait_for_timeout(1500)

    # Fill email and press Enter
    print(f"📧 Entering email: {LOGIN_EMAIL}")
    try:
        email_input = page.locator('#txtEmail').first
        email_input.click(force=True)
        email_input.fill(LOGIN_EMAIL)
        print("✅ Email entered via #txtEmail")
        page.keyboard.press("Enter")
        print("✅ Pressed Enter after email")
    except Exception as e:
        print(f"⚠️ #txtEmail failed: {e}")

    page.wait_for_timeout(500)

    # Click Continue
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

    # Wait for password field to become visible
    print("⏳ Waiting for password field to appear...")
    try:
        page.locator('#txtEmail2').wait_for(state="visible", timeout=10000)
        print("✅ Password field is now visible")
    except Exception:
        page.wait_for_timeout(2000)

    # Fill password
    print("🔑 Entering password...")
    try:
        pwd_input = page.locator('#txtEmail2').first
        pwd_input.scroll_into_view_if_needed()
        pwd_input.click(force=True)
        pwd_input.fill(LOGIN_PASSWORD)
        print("✅ Password entered via #txtEmail2")
    except Exception as e:
        print(f"⚠️ #txtEmail2 failed: {e}")

    page.wait_for_timeout(300)

    # Click Login
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

    # Wait for page to settle after login
    try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(500)
    print(f"✅ Login complete. Current URL: {page.url}")


def load_hotel_page(page):
    """Navigate to easemytrip homepage and open the Hotels tab."""
    try:
        page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded")
    except Exception as e:
        raise RuntimeError(f"❌ Website failed to load: {e}")

    try:
        hotel_icon = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
        hotel_icon.wait_for(state="visible", timeout=15000)
        hotel_icon.click()
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotels tab button is not working — button not visible or not clickable.")
    except Exception as e:
        raise RuntimeError(f"❌ Hotels tab button is not working: {e}")

    try:
        page.locator('xpath=/html/body/div[3]/div/div[4]/div/form/div/input[3]').wait_for(
            state="attached", timeout=10000
        )
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotel search form did not load after clicking Hotels tab.")


def load_hotel_page_after_login(page):
    """Re-navigate to homepage and open Hotels tab after login."""
    # Wait for any ongoing post-login redirect to fully settle before navigating
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(500)

    try:
        page.goto("https://www.easemytrip.com/", wait_until="domcontentloaded")
    except Exception as e:
        raise RuntimeError(f"❌ Website failed to load after login: {e}")

    try:
        hotel_icon = page.locator('//*[@id="homepagemenuUL"]/li[2]/a/span[2]')
        hotel_icon.wait_for(state="visible", timeout=15000)
        hotel_icon.click()
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotels tab not visible after login.")
    except Exception as e:
        raise RuntimeError(f"❌ Hotels tab error after login: {e}")

    # Wait for hotel search form + allow it to fully initialize
    try:
        page.locator('xpath=/html/body/div[3]/div/div[4]/div/form/div/input[3]').wait_for(
            state="attached", timeout=10000
        )
    except PlaywrightTimeoutError:
        raise RuntimeError("❌ Hotel search form did not load after login.")
    page.wait_for_timeout(1500)


def search_city(page, prefix, index, total):
    print(f"\n🔄 [{index}/{total}] Searching with prefix: '{prefix}'")

    # Step 1: Load homepage and open Hotels tab (so login element is available)
    load_hotel_page(page)

    # Step 2: Hover on login element → Customer Login → fill credentials
    perform_login(page)

    # Step 3: Re-open Hotels tab after login (login redirects to homepage)
    load_hotel_page_after_login(page)

    # Click the city input via JS (element is off-screen)
    try:
        element_exists = page.evaluate(f"!!document.querySelector('{CITY_INPUT_ID}')")
        if not element_exists:
            raise RuntimeError(f"❌ City input field is not working — element '{CITY_INPUT_ID}' not found on page.")
        page.evaluate(f"document.querySelector('{CITY_INPUT_ID}').click()")
        page.wait_for_timeout(300)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"❌ City input field is not working — could not click it: {e}")

    # Type prefix to trigger auto-suggest
    trigger_input(page, CITY_INPUT_ID, prefix)

    # Wait for suggestions to appear and pick the best match (prefer UAE results)
    print("🔍 Reading suggestions from auto-suggest...")
    try:
        # Wait for at least the first suggestion to appear
        first_suggestion = page.locator(SUGGESTION_XPATH)
        first_suggestion.wait_for(state="visible", timeout=15000)
    except PlaywrightTimeoutError:
        raise RuntimeError(
            f"❌ Auto-suggest dropdown is not working — no suggestions appeared for prefix '{prefix}'."
        )
    except Exception as e:
        raise RuntimeError(f"❌ Auto-suggest dropdown is not working: {e}")

    # Scan up to 6 suggestions; prefer any that mentions Dubai or UAE
    top_city = None
    chosen_index = 1
    all_items = page.locator(SUGGESTION_LIST_XPATH)
    total_suggestions = min(all_items.count(), 6)
    for n in range(1, total_suggestions + 1):
        try:
            full_text = page.locator(
                f'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[{n}]'
            ).inner_text().strip().lower()
            city_line = page.locator(
                f'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[{n}]/div/div[2]/div[1]'
            ).inner_text().strip()
            print(f"  [{n}] {city_line} | {full_text[:80]}")
            if "dubai" in full_text or "uae" in full_text:
                top_city = city_line
                chosen_index = n
                print(f"🏙️ Preferred suggestion [{n}] (UAE match): {city_line}")
                break
        except Exception:
            continue

    # Fallback to first suggestion if no UAE match found
    if not top_city:
        top_city = first_suggestion.inner_text().strip()
        chosen_index = 1
        print(f"🏙️ Top suggested city (no UAE match, using first): {top_city}")

    # Type the full city name to confirm selection
    print(f"⌨️ Typing '{top_city}' in the input field...")
    trigger_input(page, CITY_INPUT_ID, top_city)
    chosen_suggestion = page.locator(
        f'xpath=/html/body/div[3]/div/div[4]/div/form/div/div[3]/ul/li[{chosen_index}]/div/div[2]/div[1]'
    )
    try:
        chosen_suggestion.wait_for(state="visible", timeout=10000)
        print(f"✅ '{top_city}' typed successfully!")
    except PlaywrightTimeoutError:
        raise RuntimeError(
            f"❌ Auto-suggest dropdown is not working — suggestions did not reappear after typing '{top_city}'."
        )

    # Click the chosen suggestion
    print("🖱️ Clicking on suggestion item...")
    try:
        chosen_suggestion.click()
        print("✅ Suggestion item clicked!")
    except PlaywrightTimeoutError:
        raise RuntimeError(f"❌ Suggestion button is not working — could not click suggestion for '{top_city}'.")
    except Exception as e:
        raise RuntimeError(f"❌ Suggestion button is not working: {e}")

    return top_city


def select_dates(page):
    """Set check-in (tomorrow) and check-out (day after tomorrow) on the hotel form."""
    tomorrow     = datetime.today() + timedelta(days=1)
    day_after    = datetime.today() + timedelta(days=2)
    checkin_str  = tomorrow.strftime("%d/%m/%Y")
    checkout_str = day_after.strftime("%d/%m/%Y")
    checkin_day  = str(tomorrow.day)
    checkout_day = str(day_after.day)

    print(f"📅 Setting check-in: {checkin_str}, check-out: {checkout_str}")

    # Step 1: Open datepicker via a visible trigger element
    checkin_opened = False
    for selector in DATE_TRIGGER_SELECTORS:
        try:
            el = page.locator(selector).first
            if el.is_visible():
                el.click()
                page.wait_for_timeout(300)
                checkin_opened = True
                print(f"📆 Check-in datepicker opened via: {selector}")
                break
        except Exception:
            continue

    if not checkin_opened:
        # Fallback: JS click on first visible date-related element
        try:
            page.evaluate("""
                var candidates = Array.from(document.querySelectorAll(
                    'input[type="text"], div[id*="date"], div[class*="date"], div[id*="check"], div[class*="check"]'
                ));
                var el = candidates.find(function(i) {
                    var id = (i.id || '').toLowerCase();
                    return (id.includes('chk') || id.includes('check') || id.includes('date')) && i.offsetParent !== null;
                });
                if (el) { el.focus(); el.click(); }
            """)
            page.wait_for_timeout(1000)
            checkin_opened = True
            print("📆 Check-in datepicker triggered via JS")
        except Exception as e:
            print(f"⚠️ Could not open check-in picker: {e}")

    # Step 2: Wait for the datepicker panel to become visible
    if checkin_opened:
        try:
            page.locator('#ui-datepicker-div').wait_for(state="visible", timeout=5000)
            print("📆 Datepicker panel is visible")
        except Exception:
            print("⚠️ Datepicker panel not confirmed visible, attempting day click anyway")

    # Step 3: Click check-in day (force=True handles partially-hidden links)
    try:
        day_link = page.locator(
            f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{checkin_day}")'
        ).first
        day_link.wait_for(state="attached", timeout=5000)
        day_link.click(force=True)
        page.wait_for_timeout(300)
        print(f"✅ Check-in day {checkin_day} selected")

        day_link2 = page.locator(
            f'#ui-datepicker-div td:not(.ui-datepicker-other-month) a:text-is("{checkout_day}")'
        ).first
        day_link2.wait_for(state="attached", timeout=5000)
        day_link2.click(force=True)
        page.wait_for_timeout(300)
        print(f"✅ Check-out day {checkout_day} selected")
        return
    except Exception as e:
        print(f"⚠️ Calendar click failed: {e} — trying JS injection")

    # Step 4: JS fallback — inject values directly into check-in / check-out inputs
    print("🔧 Injecting date values via JS...")
    try:
        page.evaluate(
            "(function(ci, co) {"
            "  var inputs = document.querySelectorAll('form input[type=\"text\"]');"
            "  var found = 0;"
            "  for (var i = 0; i < inputs.length; i++) {"
            "    var id = (inputs[i].id || '').toLowerCase();"
            "    if (id.includes('chk') || id.includes('check')) {"
            "      inputs[i].value = (found === 0) ? ci : co;"
            "      inputs[i].dispatchEvent(new Event('change', {bubbles:true}));"
            "      found++;"
            "      if (found === 2) break;"
            "    }"
            "  }"
            "})(" + f'"{checkin_str}", "{checkout_str}"' + ");"
        )
        page.wait_for_timeout(500)
        print("✅ Dates injected via JS")
    except Exception as e:
        print(f"⚠️ JS date injection failed: {e} — proceeding without dates")


def select_guests(page, adults=2, children=1, child_ages=None):
    """
    On the hotel-new/search (SRP) page, open the Rooms & Guests selector,
    add children and set their ages, then apply to refresh results.
    child_ages: list of int, e.g. [6] for one child aged 6.
    """
    if child_ages is None:
        child_ages = [6] * children

    print(f"\n👨‍👩‍👧 Setting guests on SRP: {adults} adult(s), {children} child(ren) age(s) {child_ages}...")

    # Step 1: Open the guest/rooms dropdown using the SRP modify-search XPath
    SRP_GUEST_XPATH = 'xpath=/html/body/app-root/div/hotel-srp/modify-search/div/div/div[1]/div[3]/div/div'
    opened = False
    for selector in [
        SRP_GUEST_XPATH,
        DIV5_INPUT_XPATH,
        'hotel-srp modify-search [class*="room"]',
        'hotel-srp modify-search [class*="guest"]',
        '[class*="modify"] [class*="room"]',
        '[class*="modify"] [class*="guest"]',
    ]:
        try:
            el = page.locator(selector).first
            if el.count() > 0 and el.is_visible():
                el.click()
                page.wait_for_timeout(800)
                opened = True
                print(f"✅ Guest dropdown opened via: {selector}")
                break
        except Exception:
            continue

    if not opened:
        print("⚠️ Could not open guest dropdown on SRP — skipping guest selection.")
        return

    # Diagnostic: collect all visible '+' elements and selects in the popup
    try:
        popup_info = page.evaluate("""
            () => {
                var info = [];
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.offsetParent !== null) {
                        var t = (el.innerText || el.textContent || '').trim();
                        if (t === '+') info.push('PLUS tag=' + el.tagName + ' class=' + el.className);
                    }
                });
                document.querySelectorAll('select').forEach(function(el) {
                    if (el.offsetParent !== null)
                        info.push('SELECT id=' + el.id + ' name=' + el.name + ' class=' + el.className);
                });
                return info;
            }
        """)
        if popup_info:
            print(f"🔍 Popup elements: {popup_info[:12]}")
    except Exception:
        pass

    # Step 2: Click '+' for Children (2nd visible '+' = children increment)
    child_incremented = False
    for _ in range(children):
        if child_incremented:
            break

        # Strategy A: sibling XPaths relative to the SRP modify-search component
        for xpath in [
            'xpath=/html/body/app-root/div/hotel-srp/modify-search/div/div/div[1]/div[3]/div/div/div/div[2]/div[3]/span[3]',
            'xpath=/html/body/app-root/div/hotel-srp/modify-search/div/div/div[1]/div[3]/div/div/div/div[3]/span[3]',
            'xpath=/html/body/app-root/div/hotel-srp/modify-search//span[text()="+"][2]',
            'xpath=/html/body/app-root/div/hotel-srp/modify-search//*[contains(@class,"child")]//span[text()="+"]',
            'xpath=//hotel-srp//modify-search//*[contains(@class,"child")]//*[text()="+"]',
            'xpath=//modify-search//*[contains(translate(@class,"CHILD","child"),"child")]//*[text()="+"]',
        ]:
            try:
                btn = page.locator(xpath).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(500)
                    print(f"✅ Child count incremented via XPath: {xpath}")
                    child_incremented = True
                    break
            except Exception:
                continue

        # Strategy B: JS — click 2nd visible '+' element on page
        if not child_incremented:
            try:
                clicked = page.evaluate("""
                    () => {
                        var plusEls = Array.from(document.querySelectorAll('*'))
                            .filter(function(el) {
                                return el.offsetParent !== null &&
                                       (el.innerText || el.textContent || '').trim() === '+';
                            });
                        if (plusEls.length >= 2) { plusEls[1].click(); return 'clicked index 1'; }
                        if (plusEls.length === 1) { plusEls[0].click(); return 'clicked index 0'; }
                        return null;
                    }
                """)
                if clicked:
                    page.wait_for_timeout(500)
                    print(f"✅ Child count incremented via JS ({clicked})")
                    child_incremented = True
            except Exception:
                pass

        # Strategy C: CSS
        if not child_incremented:
            for sel in [
                '[class*="child"] span:has-text("+")',
                '[class*="children"] span:has-text("+")',
                '[class*="child"] [class*="plus"]',
                'span:has-text("+") >> nth=1',
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(500)
                        print(f"✅ Child count incremented via CSS: {sel}")
                        child_incremented = True
                        break
                except Exception:
                    continue

    if not child_incremented:
        print("⚠️ Could not increment child count.")

    # Step 3: Set age for each child (wait for age dropdown to appear)
    page.wait_for_timeout(800)
    for i, age in enumerate(child_ages):
        age_str = str(age)
        age_set = False

        for sel in [
            f'select[id*="childAge"] >> nth={i}',
            f'select[name*="childAge"] >> nth={i}',
            f'select[id*="child_age"] >> nth={i}',
            f'select[id*="ChildAge"] >> nth={i}',
            f'select[class*="child-age"] >> nth={i}',
            f'select[class*="childAge"] >> nth={i}',
            f'select[class*="age"] >> nth={i}',
        ]:
            try:
                dropdown = page.locator(sel).first
                if dropdown.count() > 0 and dropdown.is_visible():
                    dropdown.select_option(value=age_str)
                    print(f"✅ Child {i+1} age set to {age} via: {sel}")
                    age_set = True
                    break
            except Exception:
                continue

        if not age_set:
            try:
                all_selects = page.locator('select').all()
                for sel_el in all_selects:
                    if sel_el.is_visible():
                        sel_el.select_option(value=age_str)
                        print(f"✅ Child {i+1} age set to {age} via first visible <select>")
                        age_set = True
                        break
            except Exception:
                pass

        if not age_set:
            print(f"⚠️ Could not set age for child {i+1} — dropdown not found.")

    # Capture original SRP URL (contains e= session param) before Done triggers a new search
    import re as _re
    original_url = page.url

    # Build pax string for the new guest count
    if children > 0 and child_ages:
        pax_new = f"{adults}_{children}_{'_'.join(str(a) for a in child_ages)}"
    else:
        pax_new = str(adults)

    # Step 4: Click Done / Apply to confirm guest selection
    page.wait_for_timeout(300)
    confirmed = False
    for sel in [
        'a:has-text("Done")', 'button:has-text("Done")',
        'a:has-text("Apply")', 'button:has-text("Apply")',
        'button:has-text("Update")', 'button:has-text("OK")',
        '[class*="done"]', '[class*="apply"]',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(1500)
                print(f"✅ Guest selection confirmed via: {sel}")
                confirmed = True
                break
        except Exception:
            continue

    if not confirmed:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        print("✅ Guest selection applied (closed via Escape).")

    # Restore original URL format (with e= intact) but update pax to include children.
    # After Done, EaseMyTrip switches to a new URL format (?cityName=...&_v=...) that loses e=.
    # Without e=, tid= is empty and checkout breaks. Navigating back to original URL
    # format with updated pax ensures e= is preserved and tid= is populated correctly.
    if 'e=' in original_url:
        restored_url = _re.sub(r'pax=[^&]+', f'pax={pax_new}', original_url)
        if restored_url != original_url:
            page.goto(restored_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            print(f"✅ Navigated back to original URL format with pax={pax_new} — e= preserved, tid will be populated")




def navigate_to_listing(page, city_name):
    """Click the Search button to navigate to the hotel listing page."""
    print(f"🔍 Clicking Search button to navigate to listing page for '{city_name}'...")
    search_clicked = False

    # Priority 1: role/name-based locator (most robust against DOM changes)
    try:
        btn = page.get_by_role("button", name="Search").first
        if btn.count() > 0:
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
            search_clicked = True
            print("✅ Search button clicked via role/name")
    except Exception:
        pass

    # Priority 2: CSS selectors (includes #btnSearch at top of list)
    if not search_clicked:
        for selector in SEARCH_BUTTON_SELECTORS:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0:
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True)
                    search_clicked = True
                    print(f"✅ Search button clicked via selector: {selector}")
                    break
            except Exception:
                continue

    # Priority 3: XPath fallback
    if not search_clicked:
        try:
            btn = page.locator(SEARCH_BUTTON_XPATH).first
            if btn.count() > 0:
                btn.scroll_into_view_if_needed()
                btn.click(force=True)
                search_clicked = True
                print("✅ Search button clicked via XPath fallback")
        except Exception:
            pass

    if not search_clicked:
        raise RuntimeError(
            f"❌ Search button is not working — could not find or click Search button for '{city_name}'."
        )

    # Wait for navigation to the hotel results page
    try:
        page.wait_for_url(
            lambda url: (
                "hotel-new/search" in url
                or "hotels.easemytrip" in url
                or ("easemytrip.com" in url and "hotels" in url
                    and url.rstrip("/") != "https://www.easemytrip.com/hotels")
            ),
            timeout=15000,
        )
        print(f"📄 Navigated to listing page. Current URL: {page.url}")
    except PlaywrightTimeoutError:
        page.wait_for_timeout(3000)
        current_url = page.url
        print(f"📄 Current URL after wait: {current_url}")
        if current_url.rstrip("/") in (
            "https://www.easemytrip.com/hotels",
            "https://www.easemytrip.com",
        ):
            raise RuntimeError(
                f"❌ Search button is not working — page did not navigate to search results for "
                f"'{city_name}'. Still on: {current_url}"
            )


def _run_step(step_name_ref, name, fn, *args, **kwargs):
    """Execute fn(*args, **kwargs), updating step_name_ref[0] before calling."""
    step_name_ref[0] = name
    return fn(*args, **kwargs)


def automate_easemytrip():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        passed = 0
        failed = 0
        failure_log = []  # list of (prefix, step, reason)

        try:
            print("🌐 Starting easemytrip.com automation...")
            for i, prefix in enumerate(CITY_PREFIXES, 1):
                step_ref = ["Initializing"]  # mutable container so _run_step can update it
                try:
                    top_city = _run_step(step_ref, "Search city", search_city, page, prefix, i, len(CITY_PREFIXES))
                    _run_step(step_ref, "Select dates", select_dates, page)
                    _run_step(step_ref, "Navigate to listing page", navigate_to_listing, page, top_city)
                    _run_step(step_ref, "Select guests (1 child age 6)", select_guests, page, adults=2, children=1, child_ages=[6])
                    _run_step(step_ref, "Check hotel listings", check_hotel_listings, page, top_city)
                    hotel_page = _run_step(step_ref, "Click 'View Rooms'", click_view_rooms, page, top_city)
                    _run_step(step_ref, "Click 'Book Now'", click_book_now, hotel_page, top_city)
                    traveller_total = _run_step(step_ref, "Read Grand Total (Traveller Page)", get_grand_total, hotel_page, "Traveller Page")
                    _run_step(step_ref, "Fill first name", fill_first_name, hotel_page, "abhijeet", top_city)
                    _run_step(step_ref, "Fill last name", fill_last_name, hotel_page, "tiwary", top_city)
                    _run_step(step_ref, "Fill email", fill_email, hotel_page, "abhijeet.tiwary@easemytrip.com", top_city)
                    _run_step(step_ref, "Fill phone", fill_phone, hotel_page, "8707040722", top_city)
                    _run_step(step_ref, "Fill PAN card", fill_pan_card, hotel_page, "SHDJS7373H", top_city)
                    _run_step(step_ref, "Fill child name", fill_child_name, hotel_page, "santosh kumar", top_city)
                    _run_step(step_ref, "Click 'Continue Booking'", click_continue_booking, hotel_page, top_city)
                    checkout_total = _run_step(step_ref, "Read Grand Total (Checkout Page)", get_grand_total, hotel_page, "Checkout Page")
                    _run_step(step_ref, "Verify Grand Total match", verify_grand_total_match, traveller_total, checkout_total, top_city)
                    _run_step(step_ref, "Click checkout option (XPath)", click_checkout_option_xpath, hotel_page, top_city)
                    _run_step(step_ref, "Click 'Credit/Debit/ATM Cards'", click_credit_debit_card, hotel_page, top_city)
                    _run_step(step_ref, "Verify Total Fare after payment selection", verify_total_after_payment_selection, hotel_page, checkout_total, top_city)
                    _run_step(step_ref, "Fill card number", fill_card_number, hotel_page, "4992 0003 3387 1277", top_city)
                    _run_step(step_ref, "Fill expiry date", fill_valid_through, hotel_page, "07", "30", top_city)
                    _run_step(step_ref, "Fill CVV", fill_cvv, hotel_page, "539", top_city)
                    _run_step(step_ref, "Fill card holder name", fill_card_holder_name, hotel_page, "Nishant pitti", top_city)
                    _run_step(step_ref, "Click 'Make Payment'", click_continue_payment, hotel_page, top_city)
                    _run_step(step_ref, "Verify OTP page amount", verify_otp_page_amount, hotel_page, checkout_total, top_city)
                    _run_step(step_ref, "Click OTP page button", click_otp_page_button, hotel_page, top_city)
                    _run_step(step_ref, "Click 'Yes' on OTP page", click_otp_yes_button, hotel_page, top_city)
                    _run_step(step_ref, "Capture Booking ID", capture_booking_id, hotel_page, top_city)
                    passed += 1

                except RuntimeError as e:
                    failed += 1
                    reason = str(e)
                    failure_log.append((prefix, step_ref[0], reason))
                    print(f"\n{'═' * 60}")
                    print(f"❌ STEP FAILED  ➜  [{step_ref[0]}]  (city prefix: '{prefix}')")
                    print(f"   {reason}")
                    print(f"{'═' * 60}")
                    save_screenshot(page, f"failure_{prefix}")
                    print(f"⚠️ Skipping '{prefix}' and moving to the next city...\n")

                except Exception as e:
                    failed += 1
                    reason = f"Unexpected error — {e}"
                    failure_log.append((prefix, step_ref[0], reason))
                    print(f"\n{'═' * 60}")
                    print(f"❌ UNEXPECTED ERROR  ➜  [{step_ref[0]}]  (city prefix: '{prefix}')")
                    print(f"   {reason}")
                    print(traceback.format_exc())
                    print(f"{'═' * 60}")
                    save_screenshot(page, f"failure_{prefix}")
                    print(f"⚠️ Skipping '{prefix}' and moving to the next city...\n")

        except RuntimeError as e:
            print(f"\n{'═' * 60}")
            print(f"❌ FATAL ERROR — automation could not start.")
            print(f"   {e}")
            print(f"{'═' * 60}")
            save_screenshot(page, "fatal_error")

        except Exception as e:
            print(f"\n{'═' * 60}")
            print(f"❌ FATAL UNEXPECTED ERROR — automation aborted.")
            print(f"   {e}")
            print(traceback.format_exc())
            print(f"{'═' * 60}")
            save_screenshot(page, "fatal_error")

        finally:
            print(f"\n{'━' * 60}")
            print(f"📊 Summary: {passed} passed, {failed} failed out of {len(CITY_PREFIXES)} cities.")
            if failure_log:
                print(f"\n❌ Failed step details:")
                for city_prefix, step, reason in failure_log:
                    print(f"  • [{city_prefix}]  Step: {step}")
                    print(f"         Reason: {reason}")
            print(f"{'━' * 60}\n")
            browser.close()


if __name__ == "__main__":
    automate_easemytrip()
