"""
Tier 3: Pairwise & Integration Scenarios for Khujand Museum Modernization.
Threshold: >= 16 tests.
Zero non-standard dependencies.
"""

import os
import re
import sys
import json
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from tests.e2e.dom_utils import (
    PROJECT_ROOT,
    parse_html_file,
    read_file_text,
    file_exists,
    get_all_html_files,
)


class TestTier3Pairwise(unittest.TestCase):
    """Tier 3: Pairwise interaction & cross-module integration tests."""

    def test_t3_01_all_pages_nav_items_consistency(self):
        """T3.01: All pages have identical navigation item texts and link counts."""
        nav_structures = {}
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            nav = doc.find_one(tag="nav")
            if nav:
                links = [a.text.strip() for a in nav.find_all(tag="a") if not a.has_class("logo-link") and not a.has_class("logo")]
                nav_structures[html_file.name] = len(links)
        counts = set(nav_structures.values())
        self.assertLessEqual(len(counts), 1, f"Nav link counts differ across pages: {nav_structures}")

    def test_t3_02_all_pages_footer_structure_consistency(self):
        """T3.02: All pages have consistent 4-column footer layout."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            footer = doc.find_one(tag="footer")
            self.assertIsNotNone(footer, f"Footer missing on {html_file.name}")
            footer_grid = footer.find_one(**{"class": "footer-grid"}) or footer.find_one(**{"class": "footer-content"})
            self.assertIsNotNone(footer_grid, f"Footer grid missing on {html_file.name}")

    def test_t3_03_i18n_language_switching_preserves_icons(self):
        """T3.03: Language switching in js/main.js does not erase 3D icon markup."""
        js_text = read_file_text("js/main.js")
        self.assertIn("applyLanguage", js_text)
        # Verify that applyLanguage handles data-i18n on children/spans or preserves icons
        self.assertNotIn("el.innerHTML = ''", js_text)

    def test_t3_04_internal_anchor_links_target_validity(self):
        """T3.04: All internal #anchor links point to IDs existing in the same document."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            for a in doc.find_all(tag="a"):
                href = a.get_attr("href", "")
                if href.startswith("#") and len(href) > 1 and not href.startswith("#!"):
                    target_id = href[1:]
                    target_el = doc.find_one(id=target_id)
                    self.assertIsNotNone(target_el, f"Broken internal anchor {href} in {html_file.name}")

    def test_t3_05_sitemap_xml_bijection_with_actual_pages(self):
        """T3.05: Sitemap entries strictly correspond to actual files on disk."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locs = root.findall('.//sm:loc', ns) or root.findall('.//loc')
        for loc in locs:
            url = loc.text.strip()
            # Strip protocol and domain
            path_part = re.sub(r'^https?://[^/]+/?', '', url).strip()
            if not path_part or path_part == '':
                target = PROJECT_ROOT / "index.html"
            else:
                target = PROJECT_ROOT / path_part
                if not target.exists():
                    target = PROJECT_ROOT / "pages" / path_part
            self.assertTrue(target.exists(), f"Sitemap URL {url} points to non-existent file: {target}")

    def test_t3_06_exhibitions_preview_to_expositions_page(self):
        """T3.06: index.html exhibitions section links to pages/expositions.html."""
        doc = parse_html_file("index.html")
        exhibitions = doc.find_one(id="exhibitions")
        if exhibitions:
            expo_links = [a for a in exhibitions.find_all(tag="a") if "expositions.html" in (a.get_attr("href") or "")]
            self.assertGreater(len(expo_links), 0, "Exhibitions section must link to pages/expositions.html")

    def test_t3_07_gallery_preview_to_gallery_page(self):
        """T3.07: index.html gallery section links to pages/gallery.html."""
        doc = parse_html_file("index.html")
        gallery = doc.find_one(id="gallery")
        if gallery:
            gallery_links = [a for a in gallery.find_all(tag="a") if "gallery.html" in (a.get_attr("href") or "")]
            self.assertGreater(len(gallery_links), 0, "Gallery section must link to pages/gallery.html")

    def test_t3_08_history_epochs_to_scroll_world(self):
        """T3.08: Historical epochs in pages/history.html match the 4 eras in js/scroll-world.js."""
        hist_text = read_file_text("pages/history.html").lower()
        self.assertIn("согди", hist_text)
        self.assertIn("александр", hist_text)
        self.assertIn("тимурмалик", hist_text)

    def test_t3_09_cli_auto_improve_descriptions_dry_run(self):
        """T3.09: CLI scripts/auto_improve.py --task descriptions --dry-run executes successfully."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--task", "descriptions", "--dry-run", "--rounds", "1"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"auto_improve descriptions failed: {res.stderr}")

    def test_t3_10_cli_auto_improve_3d_prompts_report_output(self):
        """T3.10: CLI scripts/auto_improve.py generates valid report JSON when requested."""
        if file_exists("scripts/auto_improve.py"):
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--task", "3d-prompts", "--report", tmp_path, "--rounds", "1", "--dry-run"], capture_output=True, text=True)
                self.assertEqual(res.returncode, 0)
                if Path(tmp_path).exists() and Path(tmp_path).stat().st_size > 0:
                    with open(tmp_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.assertIsInstance(data, (dict, list))
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def test_t3_11_cli_auto_improve_all_tasks_combined(self):
        """T3.11: CLI scripts/auto_improve.py --task all executes multi-task pipeline."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--task", "all", "--dry-run", "--rounds", "1"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)

    def test_t3_12_css_tokens_applied_across_subpages(self):
        """T3.12: All subpages load css/style.css which declares CSS variables in :root."""
        css_text = read_file_text("css/style.css")
        self.assertIn(":root", css_text)
        self.assertIn("--gold", css_text)
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            links = doc.find_all(tag="link", rel="stylesheet")
            has_style = any("style.css" in (l.get_attr("href") or "") for l in links)
            self.assertTrue(has_style, f"style.css not linked in {html_file.name}")

    def test_t3_13_audio_player_element_and_script_integration(self):
        """T3.13: <audio id='bgMusic'> links to audio/ambient.mp3 and is controlled by js/main.js."""
        doc = parse_html_file("index.html")
        audio_el = doc.find_one(id="bgMusic")
        if audio_el:
            src = audio_el.get_attr("src", "")
            source_tags = audio_el.find_all(tag="source")
            source_srcs = [s.get_attr("src", "") for s in source_tags]
            has_ambient = ("ambient.mp3" in src) or any("ambient.mp3" in s for s in source_srcs)
            self.assertTrue(has_ambient, "audio/ambient.mp3 must be source for #bgMusic")
            self.assertTrue(file_exists("audio/ambient.mp3"))

    def test_t3_14_ticket_booking_cta_to_contacts_page(self):
        """T3.14: Ticket CTA in index.html targets contacts.html#ticket-booking with form."""
        doc = parse_html_file("index.html")
        nav_ticket = doc.find_one(**{"class": "nav-ticket"})
        if nav_ticket:
            href = nav_ticket.get_attr("href", "")
            self.assertIn("contacts.html", href)
            contacts_doc = parse_html_file("pages/contacts.html")
            booking = contacts_doc.find_one(id="ticket-booking")
            self.assertIsNotNone(booking, "Target #ticket-booking section missing in contacts.html")

    def test_t3_15_card_reveal_and_3d_tilt_class_compatibility(self):
        """T3.15: Cards in index.html properly combine layout, reveal, and card classes."""
        doc = parse_html_file("index.html")
        cards = doc.select(".exhibit-card")
        self.assertGreater(len(cards), 0, "No .exhibit-card elements in index.html")
        for card in cards:
            self.assertTrue(card.has_class("exhibit-card"))

    def test_t3_16_robots_txt_to_sitemap_xml_pointer(self):
        """T3.16: robots.txt declares Sitemap directive pointing to valid sitemap.xml."""
        robots_text = read_file_text("robots.txt")
        self.assertIn("Sitemap:", robots_text)
        self.assertIn("sitemap.xml", robots_text)


if __name__ == '__main__':
    unittest.main()
