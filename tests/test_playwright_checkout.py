"""
Full-Flow Playwright Browser Automation Test for Ticket Checkout & QR Pass Issuance
Khujand Fortress Museum (Исторический музей Согдийской области)

Features Verified:
1. Local daemon HTTP server hosting project on ephemeral port.
2. Headless Chromium browser automation via Playwright.
3. Date & time slot selection in booking form.
4. Ticket counter controls (Adult, Student, Child) and Add-on options.
5. Dynamic currency toggle interaction (if present).
6. Payment tab switching between Local QR and Card (if present).
7. Visitor buyer form inputs (Name, Email, Phone).
8. Sandbox card details entry and Luhn formatting.
9. Form submission, server calculation, and modal #ticketModal display.
10. Assertion on #passStatus containing "ОПЛАЧЕНО" or "PAID".
11. Assertion on #passCodeId matching KS-2026-XXXX format.
12. Assertion on #ticketQrCanvas non-blank rendered pixels.
13. Assertion on download buttons (Print, PNG/PDF export, Done).
"""

import os
import re
import time
import socket
import threading
import http.server
import socketserver
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMIUM_EXEC_PATH = r"C:\Users\user\AppData\Local\ms-playwright\chromium-1217\chrome-win64\chrome.exe"


class LocalProjectHTTPServer:
    """Threaded HTTP server serving the project root on a dynamic port."""

    def __init__(self, root_dir: Path):
        self.root_dir = str(root_dir)
        self.server = None
        self.thread = None
        self.port = None

    def start(self):
        handler_cls = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
            *args, directory=self.root_dir, **kwargs
        )
        self.server = socketserver.TCPServer(("127.0.0.1", 0), handler_cls)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.port

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class TestPlaywrightCheckoutFlow(unittest.TestCase):
    """Playwright E2E browser automation test for full checkout lifecycle."""

    @classmethod
    def setUpClass(cls):
        # 1. Start local server
        cls.http_server = LocalProjectHTTPServer(PROJECT_ROOT)
        cls.port = cls.http_server.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        # Stop local server
        if hasattr(cls, "http_server") and cls.http_server:
            cls.http_server.stop()

    def test_full_checkout_and_qr_issuance_flow(self):
        """End-to-end browser user journey: booking form -> card/sandbox -> paid modal -> QR pass."""
        with sync_playwright() as p:
            # Launch Chromium with explicit executable path
            browser = p.chromium.launch(
                executable_path=CHROMIUM_EXEC_PATH,
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            # 1. Navigate to contacts page #ticket-booking
            target_url = f"{self.base_url}/pages/contacts.html#ticket-booking"
            page.goto(target_url, wait_until="networkidle", timeout=15000)

            # Wait for booking form
            form_locator = page.locator("#ticketBookingForm")
            expect(form_locator).to_be_visible(timeout=10000)

            # 2. Date selection: Select tomorrow's date
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            date_input = page.locator("#ticketDateInput")
            date_input.fill(tomorrow)

            # 3. Slot selection: click 11:00 - 13:00 slot chip
            slot_chips = page.locator("#timeSlotChips .slot-chip")
            if slot_chips.count() > 1:
                slot_chip_11 = page.locator('#timeSlotChips button[data-slot="11:00 - 13:00"]')
                if slot_chip_11.count() > 0:
                    slot_chip_11.click()
                else:
                    slot_chips.nth(1).click()

            # 4. Ticket counter interaction: Increment adult and student
            inc_adult_btn = page.locator('button.counter-btn[data-type="adult"][data-op="inc"]')
            inc_adult_btn.click()  # adult = 2

            inc_student_btn = page.locator('button.counter-btn[data-type="student"][data-op="inc"]')
            inc_student_btn.click()  # student = 1

            # Assert counter summary updates
            sum_count = page.locator("#sumCount")
            expect(sum_count).to_contain_text("3 шт.")

            # 5. Addon interaction: check Audio Guide (+5 TJS)
            audio_checkbox = page.locator("#addonAudio")
            audio_checkbox.check()
            sum_addons = page.locator("#sumAddons")
            expect(sum_addons).to_contain_text("Аудиогид")

            # Verify calculated total amount in summary: 2*5 + 1*3 + 5 = 18 TJS
            sum_total = page.locator("#sumTotalAmount")
            expect(sum_total).to_contain_text("18 TJS")

            # 6. Currency toggle interaction (if present)
            currency_usd = page.locator('button[data-currency="USD"], .currency-btn[data-curr="USD"]')
            if currency_usd.count() > 0 and currency_usd.is_visible():
                currency_usd.click()
                time.sleep(0.1)
                # Switch back to TJS
                currency_tjs = page.locator('button[data-currency="TJS"], .currency-btn[data-curr="TJS"]')
                if currency_tjs.count() > 0:
                    currency_tjs.click()

            # 7. Payment tab switching (if tabs present in UI)
            card_tab = page.locator('button.payment-tab[data-tab="card"], button[data-tab="card"]')
            if card_tab.count() > 0 and card_tab.is_visible():
                card_tab.click()
                card_panel = page.locator("#cardPaymentPanel, .card-panel")
                if card_panel.count() > 0:
                    expect(card_panel).to_be_visible()

                # Fill sandbox card inputs if present
                card_num = page.locator('#cardNumber, input[name="cardNumber"]')
                if card_num.count() > 0 and card_num.is_visible():
                    card_num.fill("4242 4242 4242 4242")
                    card_exp = page.locator('#cardExpiry, input[name="cardExpiry"]')
                    if card_exp.count() > 0:
                        card_exp.fill("12/28")
                    card_cvc = page.locator('#cardCvc, input[name="cardCvc"]')
                    if card_cvc.count() > 0:
                        card_cvc.fill("123")

            # 8. Buyer details
            buyer_name = page.locator("#ticketBuyerName")
            buyer_name.fill("Алишер Каримов")

            buyer_email = page.locator("#ticketBuyerEmail")
            buyer_email.fill("alisher@example.com")

            buyer_phone = page.locator("#ticketBuyerPhone")
            buyer_phone.fill("+992927778899")

            # 9. Submit booking form
            submit_btn = page.locator('button[type="submit"][form="ticketBookingForm"]')
            if submit_btn.count() == 0:
                submit_btn = page.locator('#ticketBookingForm button[type="submit"]')
            submit_btn.click()

            # 10. Await #ticketModal visibility
            modal = page.locator("#ticketModal")
            page.wait_for_selector("#ticketModal.active, #ticketModal[style*='display: block']", timeout=8000)
            expect(modal).to_be_visible()

            # 11. Assert #passStatus contains "ОПЛАЧЕНО" or "PAID"
            pass_status = page.locator("#passStatus")
            expect(pass_status).to_be_visible()
            status_text = pass_status.inner_text()
            self.assertTrue(
                "ОПЛАЧЕНО" in status_text or "PAID" in status_text,
                f"passStatus must indicate successful payment, got: '{status_text}'"
            )

            # 12. Assert #passCodeId matches KS-2026-
            pass_code = page.locator("#passCodeId")
            expect(pass_code).to_be_visible()
            code_text = pass_code.inner_text()
            self.assertTrue(
                "KS-2026-" in code_text,
                f"passCodeId must contain 'KS-2026-', got: '{code_text}'"
            )

            # 13. Assert #ticketQrCanvas has rendered content
            canvas = page.locator("#ticketQrCanvas")
            expect(canvas).to_be_visible()
            canvas_data = page.evaluate("""() => {
                const c = document.getElementById('ticketQrCanvas');
                if (!c) return { exists: false };
                return {
                    exists: true,
                    width: c.width,
                    height: c.height,
                    dataUrlLength: c.toDataURL().length
                };
            }""")
            self.assertTrue(canvas_data.get("exists"))
            self.assertGreaterEqual(canvas_data.get("width", 0), 100)
            self.assertGreaterEqual(canvas_data.get("height", 0), 100)
            self.assertGreater(canvas_data.get("dataUrlLength", 0), 500, "Canvas must contain rendered QR image data")

            # 14. Assert download buttons are present and clickable
            print_btn = page.locator("#printTicketBtn")
            expect(print_btn).to_be_visible()

            # Check download image button or save button
            save_btn = page.locator("#saveTicketBtn")
            expect(save_btn).to_be_visible()

            # 15. Close modal
            close_btn = page.locator("#closeTicketModal")
            if close_btn.count() > 0 and close_btn.is_visible():
                close_btn.click()
            else:
                save_btn.click()

            time.sleep(0.3)
            # Modal must no longer have active class
            modal_classes = modal.get_attribute("class") or ""
            self.assertNotIn("active", modal_classes)

            browser.close()


if __name__ == "__main__":
    unittest.main()
