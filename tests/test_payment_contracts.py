"""
Static Contract & UI Integrity Tests for Ticket Checkout & Payment System
Khujand Fortress Museum (Исторический музей Согдийской области)

Covers:
- Payment selector tabs (Local QR: Korti Milli / Alif Pay / DC vs International Cards: Visa / MasterCard / Stripe)
- Dynamic currency selector (TJS, USD, EUR)
- Card input fields (number, expiry, cvc)
- Security indicators & badges (256-bit SSL, 3D-Secure)
- Confirmation modal (#ticketModal, #passStatus, KS-2026-XXXX, download buttons)
- 0 flat emojis invariant
- 3D icon companion <span> tag contract
- Navigation link count symmetry across all 6 pages
"""

import os
import re
import unittest
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Banned flat emojis
BANNED_EMOJIS = [
    "🏛", "🏛️",
    "🏺",
    "🎧",
    "🏰",
    "🎫",
    "📍",
    "📞",
    "📧",
    "⭐",
    "🔊",
    "💳",
    "🔒",
    "💰",
    "🎟",
    "🎟️"
]

ALL_PAGES = [
    "index.html",
    "pages/expositions.html",
    "pages/history.html",
    "pages/events.html",
    "pages/gallery.html",
    "pages/contacts.html"
]


def read_text(rel_path: str) -> str:
    path = PROJECT_ROOT / rel_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


class TestTicketModalAndPassContracts(unittest.TestCase):
    """Test modal #ticketModal structure, pass elements, and download actions."""

    def setUp(self):
        self.contacts_html = read_text("pages/contacts.html")
        self.tickets_js = read_text("js/modules/tickets.js")
        self.main_js = read_text("js/main.js")

    def test_ticket_modal_container_exists(self):
        """#ticketModal container exists in pages/contacts.html with appropriate classes."""
        self.assertIn('id="ticketModal"', self.contacts_html, "#ticketModal container must exist in contacts.html")
        self.assertIn('class="ticket-modal-backdrop"', self.contacts_html)
        self.assertIn('class="ticket-pass"', self.contacts_html)

    def test_pass_status_pill_exists_with_paid_indicator(self):
        """#passStatus element exists for displaying payment status pill."""
        self.assertIn('id="passStatus"', self.contacts_html, "#passStatus must exist in ticket modal")
        self.assertIn("ОПЛАЧЕНО", self.contacts_html, "Default or simulated ticket pass contains 'ОПЛАЧЕНО'")

    def test_pass_code_id_matches_ks_format(self):
        """#passCodeId element exists and template displays KS-2026-XXXX format."""
        self.assertIn('id="passCodeId"', self.contacts_html, "#passCodeId element must exist in ticket modal")
        match = re.search(r'id="passCodeId"[^>]*>([^<]+)<', self.contacts_html)
        self.assertIsNotNone(match, "#passCodeId must contain initial placeholder text")
        code_text = match.group(1).strip()
        self.assertTrue(code_text.startswith("KS-2026-"), f"Booking code '{code_text}' must match KS-2026- prefix")

    def test_ticket_qr_canvas_exists(self):
        """#ticketQrCanvas exists with 2D dimensions for dynamic rendering."""
        self.assertIn('id="ticketQrCanvas"', self.contacts_html)
        match = re.search(r'<canvas[^>]*id="ticketQrCanvas"[^>]*>', self.contacts_html)
        self.assertIsNotNone(match, "#ticketQrCanvas tag must be present in contacts.html")

    def test_download_and_print_buttons_exist(self):
        """Print button and download image/pdf buttons exist in DOM or module injection."""
        self.assertIn('id="printTicketBtn"', self.contacts_html, "#printTicketBtn must exist in contacts.html")
        # Module tickets.js injects #downloadTicketImageBtn or markup contains download buttons
        has_download_btn = (
            'downloadTicketImageBtn' in self.contacts_html or
            'downloadTicketPdfBtn' in self.contacts_html or
            'downloadTicketImageBtn' in self.tickets_js or
            'downloadTicketPdfBtn' in self.tickets_js
        )
        self.assertTrue(has_download_btn, "Ticket modal must provide PDF or PNG download action")

    def test_print_stylesheet_contract_in_css(self):
        """@media print styles isolate .ticket-pass for clean printer / PDF output."""
        style_css = read_text("css/style.css")
        self.assertIn("@media print", style_css)
        self.assertIn(".ticket-pass", style_css)


class TestZeroFlatEmojisAnd3DIconsIntegrity(unittest.TestCase):
    """Verify zero flat emojis and strict 3D claymorphism icon companion contracts."""

    def test_contacts_has_zero_flat_emojis(self):
        """pages/contacts.html must not contain any flat Unicode emojis."""
        html = read_text("pages/contacts.html")
        for emoji in BANNED_EMOJIS:
            self.assertNotIn(
                emoji,
                html,
                f"Banned flat emoji '{emoji}' found in pages/contacts.html; must use .clay-icon-3d WebP image."
            )

    def test_main_js_translations_have_zero_flat_emojis(self):
        """js/main.js translation dictionaries must not contain flat emojis."""
        js_code = read_text("js/main.js")
        for emoji in BANNED_EMOJIS:
            self.assertNotIn(
                emoji,
                js_code,
                f"Banned flat emoji '{emoji}' found in js/main.js dictionaries."
            )

    def test_3d_icon_companion_span_contract_preserved(self):
        """Data-i18n attributes must be placed on companion <span> tags, not parent container enclosing .clay-icon-3d."""
        html = read_text("pages/contacts.html")
        # Scan for elements with clay-icon-3d
        icon_matches = re.finditer(r'<img[^>]*class="[^"]*clay-icon-3d[^"]*"[^>]*>', html)
        for m in icon_matches:
            img_tag = m.group(0)
            self.assertIn("alt=", img_tag, f"Icon {img_tag} must have alt attribute")
            self.assertIn(".webp", img_tag, f"Icon {img_tag} must reference a local .webp file")

        # Verify companion span pattern on checkout submit button
        checkout_btn_match = re.search(r'<button[^>]*form="ticketBookingForm"[^>]*>([\s\S]*?)</button>', html)
        if checkout_btn_match:
            btn_inner = checkout_btn_match.group(1)
            self.assertIn("clay-icon-3d", btn_inner)
            self.assertIn("<span data-i18n=", btn_inner, "Button label must be inside companion <span> tag")


class TestNavigationLinkCountSymmetry(unittest.TestCase):
    """Invariant test: Nav link count symmetry across all 6 pages (test_t3_01)."""

    def test_nav_link_count_strictly_identical_across_all_pages(self):
        """Nav links in <header> <nav> must be strictly symmetrical across all 6 pages."""
        counts = {}
        for rel_path in ALL_PAGES:
            html = read_text(rel_path)
            self.assertTrue(len(html) > 0, f"Page {rel_path} must exist and be readable")
            nav_match = re.search(r'<nav[^>]*>([\s\S]*?)</nav>', html)
            self.assertIsNotNone(nav_match, f"Page {rel_path} must contain a <nav> element")
            nav_content = nav_match.group(1)
            # Find all non-logo <a> tags
            links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', nav_content)
            # Exclude brand logo link
            content_links = [l for l in links if 'class="logo"' not in l[0] and 'class="nav-logo"' not in l[0]]
            counts[rel_path] = len(content_links)

        # Assert all counts equal
        distinct_counts = set(counts.values())
        self.assertEqual(
            len(distinct_counts),
            1,
            f"Nav link count mismatch across pages! Counts: {counts}"
        )


class TestPaymentSelectorAndCheckoutFormContracts(unittest.TestCase):
    """Static contracts for Step 5 Payment Selectors, Currency Switcher, and Card Inputs."""

    def setUp(self):
        self.contacts_html = read_text("pages/contacts.html")

    @pytest.mark.xfail(reason="Milestone P2: Frontend Checkout UI tabs pending implementation in contacts.html", strict=False)
    def test_payment_selector_tabs_exist_with_local_and_card_options(self):
        """Form must have payment selector tabs for Local (Korti Milli / Alif / DC) and International (Visa / MC / Stripe)."""
        html_lower = self.contacts_html.lower()
        has_korti_milli = "корти милли" in html_lower or "korti" in html_lower or "alif" in html_lower
        has_card_option = "visa" in html_lower or "mastercard" in html_lower or "stripe" in html_lower
        has_tabs = "payment-tab" in self.contacts_html or "pay-tab" in self.contacts_html or 'role="tablist"' in self.contacts_html
        self.assertTrue(
            has_tabs and has_korti_milli and has_card_option,
            "Payment selector tabs (Local: Korti Milli/Alif/DC vs Card: Visa/MasterCard/Stripe) must exist in contacts.html"
        )

    @pytest.mark.xfail(reason="Milestone P2: Dynamic currency selector pending implementation in contacts.html", strict=False)
    def test_dynamic_currency_selector_exists(self):
        """Dynamic currency switcher (TJS, USD, EUR) exists in contacts.html booking form."""
        has_currency_toggle = (
            "currency" in self.contacts_html.lower() and
            ("tjs" in self.contacts_html or "смн" in self.contacts_html.lower()) and
            ("usd" in self.contacts_html or "eur" in self.contacts_html)
        )
        self.assertTrue(has_currency_toggle, "Currency selector for TJS/USD/EUR must exist in contacts.html")

    @pytest.mark.xfail(reason="Milestone P2: Card input fields pending implementation in contacts.html", strict=False)
    def test_card_input_fields_exist(self):
        """Card number, expiration date, and CVC input fields exist in card payment panel."""
        has_card_num = (
            'id="cardNumber"' in self.contacts_html or
            'name="cardNumber"' in self.contacts_html or
            'data-card="number"' in self.contacts_html
        )
        has_card_exp = (
            'id="cardExpiry"' in self.contacts_html or
            'name="cardExpiry"' in self.contacts_html or
            'data-card="expiry"' in self.contacts_html
        )
        has_card_cvc = (
            'id="cardCvc"' in self.contacts_html or
            'name="cardCvc"' in self.contacts_html or
            'data-card="cvc"' in self.contacts_html
        )
        self.assertTrue(has_card_num and has_card_exp and has_card_cvc, "Card input fields (number, expiry, cvc) must exist")

    def test_security_badges_exist_near_checkout_form(self):
        """Security indicator or trust badge is displayed near booking form."""
        html = self.contacts_html
        has_security_note = (
            "icon-lock-3d.webp" in html or
            "security" in html.lower() or
            "ssl" in html.lower() or
            "безопасн" in html.lower()
        )
        self.assertTrue(has_security_note, "Security indicator/badge must be visible near checkout form")


if __name__ == "__main__":
    unittest.main()
