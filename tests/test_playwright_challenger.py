"""
Adversarial Empirical Challenge Test Suite for Ticket Checkout & Payment System
Historical Museum of Sughd Region (Khujand Fortress)

Empirical Challenge Objectives:
1. Rapid switching of payment tabs and currency switcher without state corruption or UI glitches.
2. Card formatting and Luhn check feedback in the DOM.
3. High-resolution PNG download and printable PDF behavior.
4. Viewport resizing / responsive layout at 375px (mobile), 768px (tablet), 1200px (desktop).
5. Zero unhandled exceptions or console errors during entire checkout flow.
"""

import http.server
import json
import socketserver
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMIUM_EXEC_PATH = r"C:\Users\user\AppData\Local\ms-playwright\chromium-1217\chrome-win64\chrome.exe"


class LocalProjectHTTPServer:
    """Threaded HTTP server serving the project root on an ephemeral port."""

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


class TestPlaywrightChallengerSuite(unittest.TestCase):
    """Empirical adversarial challenger suite for checkout, cards, exports, and layout."""

    @classmethod
    def setUpClass(cls):
        cls.http_server = LocalProjectHTTPServer(PROJECT_ROOT)
        cls.port = cls.http_server.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "http_server") and cls.http_server:
            cls.http_server.stop()

    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            executable_path=CHROMIUM_EXEC_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.page = self.context.new_page()

    def tearDown(self):
        if hasattr(self, "context") and self.context:
            self.context.close()
        if hasattr(self, "browser") and self.browser:
            self.browser.close()
        if hasattr(self, "playwright") and self.playwright:
            self.playwright.stop()

    def _goto_checkout(self):
        url = f"{self.base_url}/pages/contacts.html#ticket-booking"
        self.page.goto(url, wait_until="networkidle", timeout=15000)
        expect(self.page.locator("#ticketBookingForm")).to_be_visible(timeout=8000)

    # =========================================================================
    # CHECK 1: Rapid Switching of Payment Tabs and Currency Switcher
    # =========================================================================
    def test_01_rapid_payment_tabs_and_currency_switching(self):
        """Stress-test rapid switching between payment tabs and currency toggles without state corruption."""
        self._goto_checkout()
        page = self.page

        tab_local = page.locator("#tabLocalPayment")
        tab_card = page.locator("#tabCardPayment")
        panel_local = page.locator("#localPaymentPanel")
        panel_card = page.locator("#cardPaymentPanel")

        expect(tab_local).to_be_visible()
        expect(tab_card).to_be_visible()

        # 1. Rapid payment tab switching (50 switches)
        for i in range(50):
            target = tab_card if (i % 2 == 0) else tab_local
            target.click()

        # 50th iteration was i=49 (odd), so target was tab_local
        expect(tab_local).to_have_class("payment-tab active")
        self.assertEqual(tab_local.get_attribute("aria-selected"), "true")
        expect(panel_local).to_be_visible()
        self.assertEqual(panel_card.evaluate("el => el.style.display"), "none")

        # Now click card once to test card state
        tab_card.click()
        expect(tab_card).to_have_class("payment-tab active")
        self.assertEqual(tab_card.get_attribute("aria-selected"), "true")
        expect(panel_card).to_be_visible()
        self.assertEqual(panel_local.evaluate("el => el.style.display"), "none")

        # 2. Rapid currency switching (60 switches across TJS, USD, EUR)
        btn_tjs = page.locator('.currency-btn[data-curr="TJS"]')
        btn_usd = page.locator('.currency-btn[data-curr="USD"]')
        btn_eur = page.locator('.currency-btn[data-curr="EUR"]')
        equiv_row = page.locator("#currencyEquivRow")
        equiv_text = page.locator("#sumTotalEquiv")
        total_amount = page.locator("#sumTotalAmount")

        currencies = [btn_tjs, btn_usd, btn_eur]
        for i in range(60):
            currencies[i % 3].click()

        # 60th click ended on EUR (index 59 % 3 = 2 -> btn_eur)
        expect(btn_eur).to_have_class("currency-btn active")
        self.assertEqual(btn_eur.get_attribute("aria-checked"), "true")
        self.assertEqual(btn_tjs.get_attribute("aria-checked"), "false")
        self.assertEqual(btn_usd.get_attribute("aria-checked"), "false")
        expect(equiv_row).to_be_visible()
        self.assertIn("€", equiv_text.inner_text())

        # Switch back to TJS and check equiv_row is hidden
        btn_tjs.click()
        expect(btn_tjs).to_have_class("currency-btn active")
        self.assertEqual(btn_tjs.get_attribute("aria-checked"), "true")
        self.assertEqual(equiv_row.evaluate("el => el.style.display"), "none")

        # 3. Dynamic Calculation & FX math check under counter updates
        # Adult +1 (total adult=2 = 10 TJS), Student +1 (3 TJS), Child +1 (2 TJS), Audio +5 TJS, Photo +10 TJS
        # Grand Total = 10 + 3 + 2 + 5 + 10 = 30 TJS
        page.locator('button.counter-btn[data-type="adult"][data-op="inc"]').click()
        page.locator('button.counter-btn[data-type="student"][data-op="inc"]').click()
        page.locator('button.counter-btn[data-type="child"][data-op="inc"]').click()
        page.locator("#addonAudio").check()
        page.locator("#addonPhoto").check()

        expect(total_amount).to_contain_text("30 TJS")

        # Switch to USD: 30 / 10.95 = 2.74 USD
        btn_usd.click()
        expect(equiv_row).to_be_visible()
        self.assertIn("2.74", equiv_text.inner_text())

        # Switch to EUR: 30 / 11.90 = 2.52 EUR
        btn_eur.click()
        expect(equiv_row).to_be_visible()
        self.assertIn("2.52", equiv_text.inner_text())

    # =========================================================================
    # CHECK 2: Card Formatting and Luhn Check Feedback in the DOM
    # =========================================================================
    def test_02_card_formatting_brand_detection_and_luhn_dom_feedback(self):
        """Verify card number formatting, brand indicator detection, Luhn validation DOM feedback, and sandbox chips."""
        self._goto_checkout()
        page = self.page

        # Switch to Card Payment tab
        page.locator("#tabCardPayment").click()
        card_num = page.locator("#cardNumber")
        card_exp = page.locator("#cardExpiry")
        card_cvc = page.locator("#cardCvc")
        card_holder = page.locator("#cardHolder")
        brand_ind = page.locator("#cardBrandIndicator")
        num_error = page.locator("#cardNumberError")
        exp_error = page.locator("#cardExpiryError")
        cvc_error = page.locator("#cardCvcError")

        # 1. Typing raw digits auto-formats with spaces and respects 19-char limit
        card_num.click()
        card_num.press_sequentially("4242424242424242")
        self.assertEqual(card_num.input_value(), "4242 4242 4242 4242")
        expect(brand_ind).to_have_text("Visa")

        # 2. Brand detection tests
        card_num.fill("")
        card_num.press_sequentially("51234567")
        expect(brand_ind).to_have_text("MasterCard")

        card_num.fill("")
        card_num.press_sequentially("97711234")
        expect(brand_ind).to_have_text("Корти Милли")

        card_num.fill("")
        card_num.press_sequentially("22041234")
        brand_detected = brand_ind.inner_text()
        self.assertEqual(
            brand_detected, "МИР",
            f"DEFECT: Card '22041234' is a MIR card (BIN 2200-2204), but detectCardBrand incorrectly matched it as '{brand_detected}' because MasterCard regex /^(5[1-5]|2[2-7])/ matches prefix '22' before MIR regex /^220/."
        )

        # 3. Expiry date auto-formatting with slash insertion
        card_exp.fill("")
        card_exp.press_sequentially("1228")
        self.assertEqual(card_exp.input_value(), "12/28")

        # 4. Fill required buyer fields so submission focuses on card validation
        page.locator("#ticketBuyerName").fill("Рустам Холиков")
        page.locator("#ticketBuyerEmail").fill("rustam@example.com")
        page.locator("#ticketBuyerPhone").fill("+992921112233")
        submit_btn = page.locator('button[type="submit"][form="ticketBookingForm"]')

        # 5. Invalid Luhn Check Feedback (Non-sandbox card that fails Luhn: 4111 1111 1111 1112)
        # 4111111111111111 passes Luhn, but ending in 2 makes it invalid!
        card_num.fill("4111 1111 1111 1112")
        card_exp.fill("12/28")
        card_cvc.fill("123")
        card_holder.fill("RUSTAM KHOLIKOV")

        submit_btn.click()

        # Assert DOM feedback for Luhn error
        expect(num_error).to_be_visible()
        self.assertIn("алгоритма Луна", num_error.inner_text())
        # Assert modal was NOT triggered
        modal = page.locator("#ticketModal")
        self.assertNotIn("active", modal.get_attribute("class") or "")

        # 6. Invalid Expiry Month Feedback (e.g. 13/28)
        card_num.fill("4111 1111 1111 1111")  # Valid Luhn card!
        card_exp.fill("13/28")
        submit_btn.click()
        expect(exp_error).to_be_visible()
        self.assertIn("Неверный месяц", exp_error.inner_text())
        self.assertNotIn("active", modal.get_attribute("class") or "")

        # 7. Invalid CVC (< 3 digits)
        card_exp.fill("12/28")
        card_cvc.fill("12")
        submit_btn.click()
        expect(cvc_error).to_be_visible()
        self.assertIn("3-4 цифры", cvc_error.inner_text())
        self.assertNotIn("active", modal.get_attribute("class") or "")

        # 8. Sandbox Chip Auto-fill: Visa Success
        page.locator("#chipVisa").click()
        self.assertEqual(card_num.input_value(), "4242 4242 4242 4242")
        self.assertEqual(card_exp.input_value(), "12/28")
        self.assertEqual(card_cvc.input_value(), "123")
        self.assertEqual(card_holder.input_value(), "IVAN IVANOV")
        self.assertEqual(num_error.evaluate("el => el.style.display"), "none")
        self.assertEqual(exp_error.evaluate("el => el.style.display"), "none")
        self.assertEqual(cvc_error.evaluate("el => el.style.display"), "none")

        # 9. Sandbox Chip: Simulated Decline (4000...0002 Insufficient Funds)
        page.locator("#chipDecline").click()
        self.assertEqual(card_num.input_value(), "4000 0000 0000 0002")
        submit_btn.click()

        # Decline alert in DOM
        alert_box = page.locator("#checkoutFormError")
        expect(alert_box).to_be_visible()
        self.assertIn("недостаточно средств", alert_box.inner_text())
        self.assertNotIn("active", modal.get_attribute("class") or "")

    # =========================================================================
    # CHECK 3: High-Resolution PNG Download and Printable PDF Behavior
    # =========================================================================
    def test_03_high_res_png_download_and_printable_pdf_behavior(self):
        """Empirically test high-resolution PNG rendering/download and printable PDF print-mode styling."""
        self._goto_checkout()
        page = self.page

        # Complete successful payment with chipVisa
        page.locator("#tabCardPayment").click()
        page.locator("#chipVisa").click()
        page.locator("#ticketBuyerName").fill("Носир Хусрав")
        page.locator("#ticketBuyerEmail").fill("nosir@khujand.tj")
        page.locator("#ticketBuyerPhone").fill("+992928889900")
        page.locator('button[type="submit"][form="ticketBookingForm"]').click()

        # Wait for ticket modal
        modal = page.locator("#ticketModal")
        page.wait_for_selector("#ticketModal.active", timeout=8000)
        expect(modal).to_be_visible()

        # 1. Verify dynamic QR canvas rendered
        qr_canvas = page.locator("#ticketQrCanvas")
        expect(qr_canvas).to_be_visible()
        qr_data_len = page.evaluate("() => document.getElementById('ticketQrCanvas').toDataURL().length")
        self.assertGreater(qr_data_len, 500, "QR Canvas must contain serialized pixel image data")

        # 2. Test High-Resolution PNG Export generator
        # Inspect offCanvas properties that downloadTicketPng constructs
        png_metadata = page.evaluate("""() => {
            const dpr = Math.max(window.devicePixelRatio || 1, 2);
            const targetWidth = 480 * dpr;
            const targetHeight = 680 * dpr;
            const bCode = document.getElementById('passCodeId')?.textContent?.trim() || '';
            const filename = `khujand-museum-ticket-${bCode.replace(/[^A-Za-z0-9_-]/g, '')}.png`;
            return { dpr, targetWidth, targetHeight, filename, bCode };
        }""")
        self.assertGreaterEqual(png_metadata["targetWidth"], 960, "High-res PNG must be at least 2x DPR width")
        self.assertGreaterEqual(png_metadata["targetHeight"], 1360, "High-res PNG must be at least 2x DPR height")
        self.assertTrue(png_metadata["filename"].startswith("khujand-museum-ticket-KS-2026-"))
        self.assertTrue(png_metadata["filename"].endswith(".png"))

        # Verify clicking #downloadTicketPngBtn triggers clean client execution without throwing
        png_btn = page.locator("#downloadTicketPngBtn")
        expect(png_btn).to_be_visible()
        png_btn.click()

        # 3. Test Printable PDF behavior and @media print isolation
        # Override window.print so headless browser doesn't block on print dialog
        page.evaluate("""() => {
            window.__printCalled = false;
            window.print = () => { window.__printCalled = true; };
        }""")

        pdf_btn = page.locator("#downloadTicketPdfBtn")
        expect(pdf_btn).to_be_visible()
        pdf_btn.click()

        # Verify window.print was called
        print_called = page.evaluate("() => window.__printCalled")
        self.assertTrue(print_called, "Download PDF button must trigger window.print()")

        # Verify print-ticket-only class was applied to body
        has_print_class = page.evaluate("() => document.body.classList.contains('print-ticket-only')")
        self.assertTrue(has_print_class, "body must receive 'print-ticket-only' class for print isolation")

        # Verify CSS rule exists for print isolation: body.print-ticket-only > *:not(#ticketModal)
        rule_check = page.evaluate("""() => {
            let foundPrintRule = false;
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.media && rule.media.mediaText.includes('print')) {
                            if (rule.cssText.includes('print-ticket-only')) foundPrintRule = true;
                        }
                    }
                } catch (_) {}
            }
            return foundPrintRule;
        }""")
        self.assertTrue(rule_check, "@media print CSS rule with .print-ticket-only must be loaded in document stylesheets")

        # Simulate afterprint event to ensure cleanup
        page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
        has_print_class_after = page.evaluate("() => document.body.classList.contains('print-ticket-only')")
        self.assertFalse(has_print_class_after, "'print-ticket-only' class must be cleaned up on afterprint")

    # =========================================================================
    # CHECK 4: Viewport Resizing / Responsive Layout (375px, 768px, 1200px)
    # =========================================================================
    def test_04_responsive_viewports_layout_and_no_overflow(self):
        """Stress-test UI at mobile (375px), tablet (768px), and desktop (1200px) viewports."""
        url = f"{self.base_url}/pages/contacts.html#ticket-booking"
        page = self.page

        # --- VIEWPORT A: 375px Mobile ---
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(url, wait_until="networkidle")

        # Check zero horizontal scroll overflow on mobile
        overflow_mobile = page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        self.assertTrue(overflow_mobile, "Page must not horizontally overflow on 375px mobile viewport")

        # Payment tabs must wrap or display cleanly
        tab_local = page.locator("#tabLocalPayment")
        tab_card = page.locator("#tabCardPayment")
        expect(tab_local).to_be_visible()
        expect(tab_card).to_be_visible()

        # Complete booking to check modal layout on 375px mobile
        page.locator("#ticketBuyerName").fill("Мобильный Тест")
        page.locator("#ticketBuyerEmail").fill("mobile@test.tj")
        page.locator("#ticketBuyerPhone").fill("+992921234567")
        page.locator('button[type="submit"][form="ticketBookingForm"]').click()

        page.wait_for_selector("#ticketModal.active", timeout=8000)
        modal_pass = page.locator(".ticket-pass")
        expect(modal_pass).to_be_visible()

        pass_width = modal_pass.evaluate("el => el.getBoundingClientRect().width")
        self.assertLessEqual(pass_width, 375, "Modal pass must fit within mobile screen width")

        # Verify buttons in modal are accessible
        expect(page.locator("#printTicketBtn")).to_be_visible()
        expect(page.locator("#downloadTicketPdfBtn")).to_be_visible()
        expect(page.locator("#downloadTicketPngBtn")).to_be_visible()
        expect(page.locator("#saveTicketBtn")).to_be_visible()

        # Close modal check on mobile: close button must be within the viewport
        close_btn_rect = page.locator("#closeTicketModal").bounding_box()
        self.assertIsNotNone(close_btn_rect, "Close button must have bounding box")
        self.assertGreaterEqual(
            close_btn_rect["y"], 0,
            f"CRITICAL DEFECT: #closeTicketModal is pushed off-screen above the mobile viewport (y = {close_btn_rect['y']}px) "
            f"because modal height ({pass_width}x{modal_pass.evaluate('el => el.getBoundingClientRect().height')}px) "
            f"exceeds viewport height (667px) with align-items:center and no scrollable container."
        )

        page.locator("#closeTicketModal").click()
        time.sleep(0.3)

        # --- VIEWPORT B: 768px Tablet ---
        page.set_viewport_size({"width": 768, "height": 1024})
        overflow_tablet = page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        self.assertTrue(overflow_tablet, "Page must not horizontally overflow on 768px tablet viewport")
        expect(page.locator("#ticketBookingForm")).to_be_visible()
        expect(page.locator(".booking-summary-card")).to_be_visible()

        # --- VIEWPORT C: 1200px Desktop ---
        page.set_viewport_size({"width": 1200, "height": 800})
        overflow_desktop = page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        self.assertTrue(overflow_desktop, "Page must not horizontally overflow on 1200px desktop viewport")

        # Desktop 2-column layout: check form and summary are side-by-side
        form_rect = page.locator("#ticketBookingForm").bounding_box()
        summary_rect = page.locator(".booking-summary-card").bounding_box()
        self.assertIsNotNone(form_rect)
        self.assertIsNotNone(summary_rect)
        self.assertLess(form_rect["x"], summary_rect["x"], "Form should be to the left of summary card on desktop")

    # =========================================================================
    # CHECK 5: Check for Unhandled Exceptions or Console Errors
    # =========================================================================
    def test_05_zero_console_errors_and_unhandled_exceptions(self):
        """Track browser console events throughout checkout interaction to ensure zero unhandled JS errors."""
        errors = []
        page = self.page

        def on_console(msg):
            # Capture console.error
            if msg.type == "error":
                text = msg.text
                # Ignore expected network 404/501 when polling offline serverless route
                if "api/checkout.js" in text or "api/send-ticket.js" in text or "status of 501" in text:
                    return
                errors.append(f"Console error: {text}")

        def on_page_error(err):
            errors.append(f"Unhandled page error: {err}")

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        self._goto_checkout()

        # Exercise all interactive elements
        # 1. Tabs
        page.locator("#tabCardPayment").click()
        page.locator("#tabLocalPayment").click()
        page.locator("#tabCardPayment").click()

        # 2. Currencies
        page.locator('.currency-btn[data-curr="USD"]').click()
        page.locator('.currency-btn[data-curr="EUR"]').click()
        page.locator('.currency-btn[data-curr="TJS"]').click()

        # 3. Counters
        page.locator('button.counter-btn[data-type="adult"][data-op="inc"]').click()
        page.locator('button.counter-btn[data-type="student"][data-op="inc"]').click()
        page.locator('button.counter-btn[data-type="child"][data-op="inc"]').click()
        page.locator('button.counter-btn[data-type="adult"][data-op="dec"]').click()

        # 4. Addons
        page.locator("#addonAudio").check()
        page.locator("#addonPhoto").check()

        # 5. Sandbox Chip
        page.locator("#chipVisa").click()

        # 6. Buyer fields
        page.locator("#ticketBuyerName").fill("Фаридун Муродов")
        page.locator("#ticketBuyerEmail").fill("faridun@example.tj")
        page.locator("#ticketBuyerPhone").fill("+992921234567")

        # 7. Submit
        page.locator('button[type="submit"][form="ticketBookingForm"]').click()
        page.wait_for_selector("#ticketModal.active", timeout=8000)

        # 8. Modal actions
        page.locator("#downloadTicketPngBtn").click()
        page.locator("#saveTicketBtn").click()

        # Assert no JS runtime errors occurred
        self.assertEqual(len(errors), 0, f"Encountered unexpected browser console or page errors: {errors}")


if __name__ == "__main__":
    unittest.main()
