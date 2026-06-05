from playwright.sync_api import sync_playwright
import random
import datetime
import re
import os

LISTING_URL = "https://www.easemytrip.com/hotels/hotels-in-new-delhi-national-capital-territory-of-delhi-india/"

def set_room(page, room_idx, adults_target, child_ages):
    """Configure room at given index (0-based): set adults and add children with ages."""
    room_box = page.locator("#roomWidget .box").nth(room_idx)

    # ── Set Adults ──
    adult_span = room_box.locator(".PlusMinus_number").first
    current = int(adult_span.inner_text())
    while current > adults_target:
        room_box.locator(".sub.hoteladultclass").click()
        page.wait_for_timeout(150)
        current -= 1
    while current < adults_target:
        room_box.locator(".add.hoteladultclass").click()
        page.wait_for_timeout(150)
        current += 1
    print(f"  Room {room_idx+1}: Adults set to {adults_target}")

    # ── Add Children with ages ──
    for idx, age in enumerate(child_ages):
        room_box.locator(".add.hotelchildclass").click()
        page.wait_for_timeout(300)
        age_select = room_box.locator(".sleact-wrap select").nth(idx)
        age_select.select_option(str(age))
        page.wait_for_timeout(150)
        print(f"  Room {room_idx+1}: Child {idx+1} age set to {age}")


def set_dates(page, checkin, checkout):
    """Set check-in and check-out dates on the listing page via jQuery datepicker."""
    page.evaluate("""(args) => {
        const ci = document.querySelector('#txtCheckInDate');
        if (ci) { $(ci).datepicker('setDate', new Date(args.cy, args.cm-1, args.cd)); $(ci).trigger('change'); }
        const co = document.querySelector('#txtCheckOutDate');
        if (co) { $(co).datepicker('setDate', new Date(args.oy, args.om-1, args.od)); $(co).trigger('change'); }
    }""", {"cy": checkin.year, "cm": checkin.month, "cd": checkin.day,
           "oy": checkout.year, "om": checkout.month, "od": checkout.day})
    page.wait_for_timeout(500)


def capture_traveller_amount(page):
    """Capture Grand Total from the traveller/review page."""
    selectors = [
        ".grand-total", ".grandTotal", ".grandtotal", ".grand_total",
        "[class*='grandTotal']", "[class*='grand_total']", "[class*='grand-total']",
        ".totalFare", ".total-fare", ".totalfare", ".fare-total",
        ".priceSection .price", ".total-price",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.wait_for(state="visible", timeout=1500)
                amt = el.inner_text().strip()
                if re.search(r'\d', amt):
                    print(f"Traveller page - Grand Total ({sel}): {amt}")
                    return amt
        except Exception:
            continue
    # Fallback: scan body text
    body = page.locator("body").inner_text()
    for pattern in [r'Grand\s*Total[^\d]*(\d[\d,]*)', r'Total\s*Fare[^\d]*(\d[\d,]*)',
                    r'Total\s*Amount[^\d]*(\d[\d,]*)']:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            print(f"Traveller page - Grand Total (parsed): {m.group(1)}")
            return m.group(1)
    print("Traveller page - Grand Total: not found")
    return None


def capture_checkout_amount(page):
    """Capture Grand Total / Total Fare from the checkout page (Angular)."""
    # Wait for Angular to render fare elements
    page.wait_for_timeout(2000)
    # Angular checkout page: .fare contains "Total Fare: Rs. XXXX",
    # .red.ng-binding contains just the numeric value
    selectors = [
        ".fare .red.ng-binding", ".fare span.red", ".red.ng-binding",
        ".fare-wrap .red", "[class*='fare'] [class*='red']",
        ".fare",
        ".grand-total", ".grandTotal", ".grand_total",
        "[class*='grandTotal']", "[class*='grand_total']",
        ".total-fare", ".totalFare",
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.wait_for(state="visible", timeout=1500)
                amt = el.inner_text().strip()
                if re.search(r'\d', amt):
                    print(f"Checkout page - Grand Total ({sel}): {amt}")
                    return amt
        except Exception:
            continue
    # Fallback: regex on page body
    body = page.locator("body").inner_text()
    for pattern in [r'Total\s*Fare[^\d]*(\d[\d,]*)', r'Grand\s*Total[^\d]*(\d[\d,]*)',
                    r'Total\s*Amount[^\d]*(\d[\d,]*)']:
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            print(f"Checkout page - Grand Total (parsed): {m.group(1)}")
            return m.group(1)
    print("Checkout page - Grand Total: not found")
    return None


def test_launch_url():
    checkin  = datetime.date.today() + datetime.timedelta(days=2)
    checkout = datetime.date.today() + datetime.timedelta(days=4)

    print(f"Check-In  : {checkin.strftime('%d %b %Y')}")
    print(f"Check-Out : {checkout.strftime('%d %b %Y')}")

    rooms = [
        {"adults": 1, "child_ages": [5]},
        {"adults": 1, "child_ages": [10]},
        {"adults": 1, "child_ages": [6]},
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})

        # ── Step 1: Launch listing page and set dates ──
        page.goto(LISTING_URL, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        print("URL launched successfully")

        print("Setting dates on listing page...")
        set_dates(page, checkin, checkout)

        # ── Steps 2–6: Select hotel, configure rooms, Modify Search (retry if sold out) ──
        tried_indices = set()

        while True:
            # If redirected back to listing (sold out), reset dates
            if "hotels-in-new-delhi" in page.url and tried_indices:
                print("Back on listing page — hotel was sold out. Picking another hotel...")
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                page.wait_for_timeout(1000)
                set_dates(page, checkin, checkout)

            # ── Step 2: Scroll and click a random (untried) View Room ──
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(800)

            view_room_locator = page.locator("xpath=//a/div[normalize-space(text())='View Room']")
            count = view_room_locator.count()
            print(f"Found {count} 'View Room' buttons")

            available = [i for i in range(count) if i not in tried_indices]
            if not available:
                print("All hotels tried — resetting tried list")
                tried_indices.clear()
                available = list(range(count))

            random_index = random.choice(available)
            tried_indices.add(random_index)
            print(f"Clicking 'View Room' at index {random_index}")

            btn = view_room_locator.nth(random_index)
            btn.scroll_into_view_if_needed()
            page.wait_for_timeout(300)

            try:
                with page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                    btn.click()
                page.wait_for_load_state("domcontentloaded", timeout=60000)
            except Exception as nav_err:
                print(f"Navigation failed for index {random_index}: {nav_err.__class__.__name__} — trying another hotel")
                page.goto(LISTING_URL, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                set_dates(page, checkin, checkout)
                continue

            page.wait_for_timeout(1500)
            print(f"Navigated to: {page.url}")

            # ── Step 3: Open Rooms/Guests selector ──
            print("Opening Rooms/Guests selector...")
            page.locator(".guests_select").click()
            page.wait_for_timeout(800)

            # ── Step 4: Configure all rooms ──
            for i, room in enumerate(rooms):
                print(f"Configuring Room {i+1}...")
                if i > 0:
                    page.locator("a.addroom:not(.exitroom):not(.removeroom)").click()
                    page.wait_for_timeout(600)
                    page.locator("#roomWidget .box").nth(i).wait_for(state="visible", timeout=5000)
                set_room(page, i, room["adults"], room["child_ages"])

            # ── Step 5: Click Done ──
            print("Clicking Done...")
            page.locator("a.addroom.exitroom").click()
            page.wait_for_timeout(800)
            summary = page.locator(".guests_selected").inner_text()
            print(f"Rooms/Guests summary: {summary}")

            # ── Step 6: Click Modify Search ──
            print("Clicking Modify Search...")
            modify_btn = page.locator("button.btnsrch")
            modify_btn.scroll_into_view_if_needed()
            modify_btn.click()
            page.wait_for_timeout(2000)
            print(f"URL after Modify Search: {page.url}")

            # ── Sold-out / search redirect check ──
            if "hotels-in-new-delhi" in page.url or "/hotel-new/search" in page.url:
                reason = "sold out" if "hotels-in-new-delhi" in page.url else "redirected to search (no direct booking)"
                print(f"Hotel {reason} — trying another hotel.")
                page.goto(LISTING_URL, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                set_dates(page, checkin, checkout)
                continue

            break  # Successfully on hotel detail page

        # ── Step 7: Click Book Now ──
        print("Clicking Book Now...")
        book_now_btn = page.locator("a.fill-btn, a.fill-btns, a:has-text('Book Now'), button:has-text('Book Now')").first
        book_now_btn.wait_for(state="visible", timeout=60000)
        book_now_btn.scroll_into_view_if_needed()
        book_now_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        print(f"Traveller page URL: {page.url}")

        # ── Capture total amount on traveller page ──
        traveller_amount = capture_traveller_amount(page)

        # ── Step 8: Fill traveller details ──
        travellers = [
            ("Abhijeet", "Tiwary"),
            ("Anshul",   "Sharma"),
            ("Manish",   "Kumar"),
            ("Santosh",  "Kumar"),
            ("Manish",   "Kumar"),
            ("Shivam",   "Kumar"),
        ]

        first_name_inputs = page.locator('input[name="txtFirstName"]')
        last_name_inputs  = page.locator('input[name="txtLastName"]')

        for idx, (first, last) in enumerate(travellers):
            first_name_inputs.nth(idx).click()
            first_name_inputs.nth(idx).fill(first)
            last_name_inputs.nth(idx).click()
            last_name_inputs.nth(idx).fill(last)
            page.wait_for_timeout(100)
            print(f"  Filled traveller {idx+1}: {first} {last}")

        # ── Step 9: Fill contact details ──
        print("Filling email and phone...")
        page.locator('input[placeholder="Enter email address"]').fill("abhijeet.tiwary@easemytrip.com")
        page.locator('input[placeholder="Enter Mobile Number"]').fill("8707040722")
        print("  Email and phone filled")

        # ── Step 10: Click Continue Booking ──
        print("Clicking Continue Booking...")
        continue_btn = page.locator("button, a").filter(has_text="Continue Booking").first
        continue_btn.scroll_into_view_if_needed()
        continue_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        print(f"URL after Continue Booking: {page.url}")

        # ── Capture total amount on checkout page ──
        checkout_amount = capture_checkout_amount(page)

        # ── Amount verification ──
        if traveller_amount and checkout_amount:
            t_norm = re.sub(r'[^\d]', '', traveller_amount)
            c_norm = re.sub(r'[^\d]', '', checkout_amount)
            if t_norm == c_norm:
                print(f"[PASS] AMOUNT MATCH -- Traveller Grand Total ({traveller_amount}) == Checkout Grand Total ({checkout_amount})")
            else:
                print(f"[FAIL] AMOUNT MISMATCH -- Traveller Grand Total ({traveller_amount}) != Checkout Grand Total ({checkout_amount})")
                screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(screenshots_dir, f"price_mismatch_{timestamp}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[Screenshot saved]: {screenshot_path}")
        else:
            print("Amount comparison skipped (one or both amounts not captured)")

        # ── Step 11: Click payment section (Net Banking) ──
        print("Clicking payment section on checkout page...")
        checkout_el = page.locator("xpath=/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[1]/div[4]/div/div[2]/div[2]")
        checkout_el.scroll_into_view_if_needed()
        checkout_el.click()
        page.wait_for_timeout(1500)
        print(f"Clicked: {checkout_el.inner_text()}")

        # ── Step 12: Select Axis Bank ──
        print("Selecting Axis Bank...")
        label_el = page.locator("xpath=/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[5]/div[1]/div[4]/div[4]/label/span[2]")
        label_el.wait_for(state="visible", timeout=30000)
        label_el.scroll_into_view_if_needed()
        label_el.click()
        page.wait_for_timeout(1000)
        print(f"Selected: {label_el.inner_text()}")

        # ── Step 13: Click Make Payment ──
        print("Clicking Make Payment...")
        make_payment_btn = page.locator("xpath=/html/body/form/div[2]/div[2]/div[1]/div[4]/div[2]/div[6]/div[5]/div[3]/div[2]")
        make_payment_btn.wait_for(state="visible", timeout=30000)
        make_payment_btn.scroll_into_view_if_needed()
        make_payment_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        print(f"URL after Make Payment: {page.url}")

        # ── Step 14: Handle Axis Bank login page ──
        print("Waiting for Axis Bank page to load...")
        page.wait_for_timeout(4000)  # Angular app needs time to render
        print(f"Axis Bank URL: {page.url}")

        print("Clicking button[2] on Axis Bank login page...")
        axis_btn = page.locator("xpath=/html/body/app-layout/app-login/div/div[3]/form/button[2]")
        axis_btn.wait_for(state="visible", timeout=60000)
        axis_btn.scroll_into_view_if_needed()
        axis_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(1000)
        try:
            print(f"Clicked Axis button: {axis_btn.inner_text()}")
        except Exception:
            print("Axis button clicked (page may have navigated)")
        print(f"Page after Axis button[2]: {page.url}")

        # ── Step 15: If still on Axis Bank, click Cancel twice ──
        if "axis" in page.url.lower() or "nbpg" in page.url.lower():
            for cancel_num in range(1, 3):
                print(f"Clicking Cancel ({cancel_num} of 2)...")
                try:
                    cancel_btn = page.locator("button:has-text('Cancel'), a:has-text('Cancel'), [class*='cancel']").first
                    cancel_btn.wait_for(state="visible", timeout=15000)
                    cancel_btn.scroll_into_view_if_needed()
                    cancel_btn.click()
                    page.wait_for_timeout(1500)
                    print(f"Cancel {cancel_num} clicked")
                except Exception as e:
                    print(f"Cancel button {cancel_num} not found: {e.__class__.__name__}")
                    break

        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(1000)
        print(f"Result page URL: {page.url}")

        # ── Step 16: Capture Booking ID from payment error page ──
        print("Capturing Booking ID from payment error page...")
        try:
            booking_id_el = page.locator("xpath=/html/body/form/div[3]/div/div[2]/div[1]/div[2]")
            booking_id_el.wait_for(state="visible", timeout=15000)
            raw_text = booking_id_el.inner_text().strip()
            match = re.search(r'(EMT\w+|\bBK\w+)', raw_text)
            booking_id = match.group(1) if match else raw_text
            print(f"Booking ID: {booking_id}")
        except Exception:
            try:
                body_text = page.locator("body").inner_text()
                m = re.search(r'Booking\s*ID\s*[:\-]?\s*(\w+)', body_text, re.IGNORECASE)
                print(f"Booking ID: {m.group(1)}" if m else f"Booking ID not found. Snippet: {body_text[:300]}")
            except Exception as e:
                print(f"Could not read page: {e}")

        page.wait_for_timeout(2000)
        browser.close()

if __name__ == "__main__":
    test_launch_url()
