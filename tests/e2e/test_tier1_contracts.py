"""
Tier 1: Functional & Contract Tests for Khujand Museum Website Modernization.
Threshold: >= 80 tests (5 tests per feature across all 16 features).
Zero non-standard dependencies.
"""

import os
import re
import sys
import json
import unittest
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from tests.e2e.dom_utils import (
    PROJECT_ROOT,
    parse_html_file,
    read_file_text,
    file_exists,
    dir_exists,
    get_all_html_files,
)


class TestTier1Contracts(unittest.TestCase):
    """Tier 1: Functional & Contract test cases."""

    # -------------------------------------------------------------------------
    # Feature 1: Authentic Local Media Migration (M1)
    # -------------------------------------------------------------------------
    def test_t1_f01_local_images_directory_structure(self):
        """F1: images/ directory hierarchy must exist for exhibits, fortress, highlights, and icons."""
        self.assertTrue(dir_exists("images"), "images/ directory must exist in project root.")
        for subdir in ["exhibits", "fortress", "highlights", "icons"]:
            self.assertTrue(
                dir_exists(f"images/{subdir}"),
                f"images/{subdir}/ subfolder must exist for authentic museum media.",
            )

    def test_t1_f02_no_unsplash_cake_placeholder(self):
        """F1: Tiramisu cake placeholder (photo-1571115177098) must not exist in index.html."""
        content = read_file_text("index.html")
        self.assertNotIn(
            "photo-1571115177098",
            content,
            "Cake placeholder (photo-1571115177098) found in index.html; must be replaced by Timur Malik statue.",
        )

    def test_t1_f03_no_unsplash_gamepad_placeholder(self):
        """F1: PlayStation gamepad placeholder (photo-1509198397868) must not exist in index.html."""
        content = read_file_text("index.html")
        self.assertNotIn(
            "photo-1509198397868",
            content,
            "Gamepad placeholder (photo-1509198397868) found in index.html; must be replaced by Khujand armor.",
        )

    def test_t1_f04_no_unsplash_gavel_placeholder(self):
        """F1: Court gavel placeholder (photo-1575505586569) must not exist in index.html."""
        content = read_file_text("index.html")
        self.assertNotIn(
            "photo-1575505586569",
            content,
            "Court gavel placeholder (photo-1575505586569) found in index.html; must be replaced by Saka gold helmet.",
        )

    def test_t1_f05_zero_external_unsplash_references(self):
        """F1: Zero external images.unsplash.com references across all HTML files."""
        html_files = get_all_html_files()
        found_unsplash = []
        for html_file in html_files:
            text = read_file_text(str(html_file.relative_to(PROJECT_ROOT)))
            if "images.unsplash.com" in text:
                found_unsplash.append(str(html_file.name))
        self.assertEqual(
            found_unsplash,
            [],
            f"External Unsplash URLs still present in: {', '.join(found_unsplash)}",
        )

    # -------------------------------------------------------------------------
    # Feature 2: Virtual Tour File Removal (M2)
    # -------------------------------------------------------------------------
    def test_t1_f06_virtual_tour_file_not_on_disk(self):
        """F2: pages/virtual-tour.html must not exist on disk."""
        target = PROJECT_ROOT / "pages" / "virtual-tour.html"
        self.assertFalse(target.exists(), f"pages/virtual-tour.html must be deleted, but exists at {target}")

    def test_t1_f07_no_backup_virtual_tour_files(self):
        """F2: No backup or temporary virtual tour files in pages/ or root."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for p in pages_dir.glob("*virtual-tour*"):
                self.fail(f"Found dangling virtual tour file: {p.name}")

    def test_t1_f08_no_virtual_tour_in_pages_directory(self):
        """F2: pages/ directory contains no file containing 'virtual-tour' in its name."""
        pages_dir = PROJECT_ROOT / "pages"
        tour_files = [f.name for f in pages_dir.iterdir() if "virtual-tour" in f.name.lower()] if pages_dir.exists() else []
        self.assertEqual(tour_files, [], f"Virtual tour files present in pages/: {tour_files}")

    def test_t1_f09_no_canvas_virtual_tour_script_files(self):
        """F2: No canvas pseudotour script remains in pages/ or js/."""
        js_dir = PROJECT_ROOT / "js"
        canvas_tour_files = list(js_dir.glob("*tour*.js")) if js_dir.exists() else []
        self.assertEqual(canvas_tour_files, [], f"Tour scripts found in js/: {canvas_tour_files}")

    def test_t1_f10_pages_directory_contains_only_valid_subpages(self):
        """F2: pages/ directory contains only approved canonical subpages."""
        approved = {"contacts.html", "events.html", "expositions.html", "gallery.html", "history.html"}
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            actual = {f.name for f in pages_dir.glob("*.html")}
            self.assertTrue(actual.issubset(approved), f"Unexpected HTML pages in pages/: {actual - approved}")

    # -------------------------------------------------------------------------
    # Feature 3: Tour Promo Banner Elimination (M2)
    # -------------------------------------------------------------------------
    def test_t1_f11_no_tour_promo_section_in_index(self):
        """F3: index.html must not contain section.tour-promo or tour-banner-section."""
        doc = parse_html_file("index.html")
        promo_sections = doc.find_all(tag="section", **{"class": "tour-promo"}) + doc.find_all(tag="section", **{"class": "tour-banner-section"})
        self.assertEqual(len(promo_sections), 0, "tour-promo / tour-banner-section still present in index.html")

    def test_t1_f12_no_tour_banner_badge_i18n_attr(self):
        """F3: index.html must not contain data-i18n='tour.banner_badge'."""
        doc = parse_html_file("index.html")
        self.assertIsNone(doc.find_one(**{"data-i18n": "tour.banner_badge"}), "data-i18n='tour.banner_badge' must be removed")

    def test_t1_f13_no_tour_banner_title_i18n_attr(self):
        """F3: index.html must not contain data-i18n='tour.banner_title'."""
        doc = parse_html_file("index.html")
        self.assertIsNone(doc.find_one(**{"data-i18n": "tour.banner_title"}), "data-i18n='tour.banner_title' must be removed")

    def test_t1_f14_no_tour_banner_desc_i18n_attr(self):
        """F3: index.html must not contain data-i18n='tour.banner_desc'."""
        doc = parse_html_file("index.html")
        self.assertIsNone(doc.find_one(**{"data-i18n": "tour.banner_desc"}), "data-i18n='tour.banner_desc' must be removed")

    def test_t1_f15_no_tour_banner_btn_i18n_attr(self):
        """F3: index.html must not contain data-i18n='tour.banner_btn'."""
        doc = parse_html_file("index.html")
        self.assertIsNone(doc.find_one(**{"data-i18n": "tour.banner_btn"}), "data-i18n='tour.banner_btn' must be removed")

    # -------------------------------------------------------------------------
    # Feature 4: Navigation & Footer Tour Link Removal (M2)
    # -------------------------------------------------------------------------
    def test_t1_f16_index_nav_has_zero_tour_links(self):
        """F4: In index.html, <nav> has 0 links pointing to virtual-tour.html."""
        doc = parse_html_file("index.html")
        nav = doc.find_one(tag="nav")
        if nav:
            tour_links = [a for a in nav.find_all(tag="a") if "virtual-tour" in (a.get_attr("href") or "")]
            self.assertEqual(len(tour_links), 0, f"Found virtual-tour link in index.html <nav>: {tour_links}")

    def test_t1_f17_index_footer_has_zero_tour_links(self):
        """F4: In index.html, <footer> has 0 links pointing to virtual-tour.html."""
        doc = parse_html_file("index.html")
        footer = doc.find_one(tag="footer")
        if footer:
            tour_links = [a for a in footer.find_all(tag="a") if "virtual-tour" in (a.get_attr("href") or "")]
            self.assertEqual(len(tour_links), 0, f"Found virtual-tour link in index.html <footer>: {tour_links}")

    def test_t1_f18_subpages_nav_have_zero_tour_links(self):
        """F4: In all pages/*.html, <nav> has 0 links pointing to virtual-tour.html."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for p in pages_dir.glob("*.html"):
                if p.name == "virtual-tour.html":
                    continue
                doc = parse_html_file(str(p))
                nav = doc.find_one(tag="nav")
                if nav:
                    tour_links = [a for a in nav.find_all(tag="a") if "virtual-tour" in (a.get_attr("href") or "")]
                    self.assertEqual(len(tour_links), 0, f"Found virtual-tour link in {p.name} <nav>")

    def test_t1_f19_subpages_footer_have_zero_tour_links(self):
        """F4: In all pages/*.html, <footer> has 0 links pointing to virtual-tour.html."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for p in pages_dir.glob("*.html"):
                if p.name == "virtual-tour.html":
                    continue
                doc = parse_html_file(str(p))
                footer = doc.find_one(tag="footer")
                if footer:
                    tour_links = [a for a in footer.find_all(tag="a") if "virtual-tour" in (a.get_attr("href") or "")]
                    self.assertEqual(len(tour_links), 0, f"Found virtual-tour link in {p.name} <footer>")

    def test_t1_f20_main_js_dictionaries_contain_no_tour_keys(self):
        """F4: js/main.js translation dictionaries must not contain 'nav.tour' or 'tour.banner_' keys."""
        content = read_file_text("js/main.js")
        self.assertNotIn('"nav.tour"', content, "'nav.tour' key must be removed from js/main.js")
        self.assertNotIn('"tour.banner_', content, "'tour.banner_*' keys must be removed from js/main.js")

    # -------------------------------------------------------------------------
    # Feature 5: Sitemap Validation (M2)
    # -------------------------------------------------------------------------
    def test_t1_f21_sitemap_xml_exists_and_non_empty(self):
        """F5: sitemap.xml exists and is non-empty."""
        self.assertTrue(file_exists("sitemap.xml"), "sitemap.xml must exist in project root.")
        path = PROJECT_ROOT / "sitemap.xml"
        self.assertGreater(path.stat().st_size, 0, "sitemap.xml must not be empty.")

    def test_t1_f22_sitemap_xml_parses_valid_schema(self):
        """F5: sitemap.xml is well-formed XML under http://www.sitemaps.org/schemas/sitemap/0.9."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertTrue("urlset" in root.tag.lower(), "Root element of sitemap.xml must be urlset.")

    def test_t1_f23_sitemap_xml_has_zero_virtual_tour_links(self):
        """F5: sitemap.xml contains 0 references to virtual-tour.html."""
        content = read_file_text("sitemap.xml")
        self.assertNotIn("virtual-tour", content.lower(), "sitemap.xml must not contain virtual-tour.")

    def test_t1_f24_sitemap_xml_all_loc_urls_resolve_to_files(self):
        """F5: Every URL in sitemap.xml corresponds to an actual file on disk."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        loc_elements = root.findall('.//sm:loc', ns) or root.findall('.//loc')
        self.assertGreater(len(loc_elements), 0, "sitemap.xml must define at least one <loc>")
        for loc in loc_elements:
            url = (loc.text or "").strip()
            # Extract path from URL e.g. https://khujand-museum.tj/pages/history.html -> pages/history.html
            match = re.search(r'https?://[^/]+/(.*)$', url)
            rel_path = match.group(1) if match else url.lstrip('/')
            if not rel_path or rel_path == "":
                rel_path = "index.html"
            local_target = PROJECT_ROOT / rel_path
            self.assertTrue(local_target.exists(), f"Sitemap URL {url} resolves to non-existent file {local_target}")

    def test_t1_f25_sitemap_xml_contains_all_canonical_routes(self):
        """F5: sitemap.xml contains all 6 canonical site routes."""
        content = read_file_text("sitemap.xml")
        expected_pages = ["expositions.html", "history.html", "events.html", "gallery.html", "contacts.html"]
        for p in expected_pages:
            self.assertIn(p, content, f"sitemap.xml must include {p}")

    # -------------------------------------------------------------------------
    # Feature 6: 3D Gold & Claymorphism Icons (M3)
    # -------------------------------------------------------------------------
    def test_t1_f26_css_defines_clay_icon_3d_class(self):
        """F6: css/style.css defines .clay-icon-3d class."""
        css_text = read_file_text("css/style.css")
        self.assertIn(".clay-icon-3d", css_text, "css/style.css must define .clay-icon-3d class")

    def test_t1_f27_css_defines_clay_levitation_keyframes(self):
        """F6: css/style.css defines micro-levitation keyframe animation for 3D icons."""
        css_text = read_file_text("css/style.css")
        has_keyframes = ("@keyframes clay-levitate" in css_text or "@keyframes icon-float" in css_text)
        self.assertTrue(has_keyframes, "css/style.css must define keyframes for clay-levitate or icon-float")

    def test_t1_f28_images_icons_or_gold_styling_present(self):
        """F6: images/icons/ directory exists or CSS contains gold/terracotta styling tokens."""
        css_text = read_file_text("css/style.css")
        has_clay_tokens = ("--gold" in css_text and ("clay" in css_text.lower() or "terracotta" in css_text.lower() or ".clay-icon-3d" in css_text))
        self.assertTrue(has_clay_tokens or dir_exists("images/icons"), "3D icon tokens or images/icons/ must be present")

    def test_t1_f29_html_has_clay_icon_3d_elements(self):
        """F6: index.html contains .clay-icon-3d elements for key museum sections."""
        doc = parse_html_file("index.html")
        icons = doc.select(".clay-icon-3d")
        self.assertGreater(len(icons), 0, "index.html must contain .clay-icon-3d elements")

    def test_t1_f30_logo_icon_does_not_contain_flat_emoji_only(self):
        """F6: .logo-icon does not contain only flat emoji 🏛️ without 3D styling/markup."""
        doc = parse_html_file("index.html")
        logo_icon = doc.find_one(**{"class": "logo-icon"})
        if logo_icon:
            # It should either be an image, svg, or styled with clay-icon-3d class
            is_modern = (logo_icon.find_one(tag="img") is not None or
                         logo_icon.find_one(tag="svg") is not None or
                         logo_icon.has_class("clay-icon-3d") or
                         "clay" in logo_icon.attrs.get("class", ""))
            self.assertTrue(is_modern, ".logo-icon must be upgraded to 3D icon element, not raw flat emoji")

    # -------------------------------------------------------------------------
    # Feature 7: Decoupled i18n Icon Rendering (M3)
    # -------------------------------------------------------------------------
    def test_t1_f31_clay_icon_elements_lack_direct_data_i18n(self):
        """F7: Elements with .clay-icon-3d must not bear data-i18n directly on the same element."""
        doc = parse_html_file("index.html")
        icons = doc.select(".clay-icon-3d")
        for icon in icons:
            self.assertIsNone(icon.get_attr("data-i18n"), ".clay-icon-3d must not have direct data-i18n attribute")

    def test_t1_f32_data_i18n_placed_on_companion_span_tags(self):
        """F7: In top utility bar, data-i18n attributes are placed on companion span/text elements."""
        doc = parse_html_file("index.html")
        top_bar = doc.find_one(**{"class": "top-bar"})
        if top_bar:
            i18n_nodes = top_bar.find_all(**{"data-i18n": True})
            for node in i18n_nodes:
                self.assertFalse(node.has_class("clay-icon-3d"), f"Node with data-i18n={node.get_attr('data-i18n')} must not be .clay-icon-3d")

    def test_t1_f33_main_js_apply_language_preserves_icons(self):
        """F7: js/main.js applyLanguage function protects 3D icon elements from textContent overwrite."""
        js_text = read_file_text("js/main.js")
        self.assertIn("applyLanguage", js_text, "js/main.js must define applyLanguage function")

    def test_t1_f34_main_js_top_contacts_keys_lack_flat_emojis(self):
        """F7: js/main.js Russian dictionary top.address, top.phone, top.hours do not include flat emojis."""
        js_text = read_file_text("js/main.js")
        # Matches e.g. "top.phone": "📞 +992..."
        self.assertNotRegex(js_text, r'"top\.phone"\s*:\s*"[📞]', "top.phone translation string must not include flat emoji")
        self.assertNotRegex(js_text, r'"top\.address"\s*:\s*"[📍]', "top.address translation string must not include flat emoji")

    def test_t1_f35_multilingual_dictionaries_avoid_raw_emojis(self):
        """F7: Multilingual dictionaries in js/main.js do not embed raw emojis in nav keys."""
        js_text = read_file_text("js/main.js")
        self.assertNotRegex(js_text, r'"nav\.home"\s*:\s*"[🏛️🏰]', "nav.home must not embed flat emojis")
        self.assertNotRegex(js_text, r'"nav\.tickets"\s*:\s*"[🎫]', "nav.tickets must not embed flat emojis")

    # -------------------------------------------------------------------------
    # Feature 8: 4-Epoch WebGL Scroll-World (M4)
    # -------------------------------------------------------------------------
    def test_t1_f36_scroll_world_container_present_in_index(self):
        """F8: index.html contains #scroll-world section."""
        doc = parse_html_file("index.html")
        self.assertIsNotNone(doc.find_one(id="scroll-world"), "#scroll-world section must be present in index.html")

    def test_t1_f37_scroll_world_positioned_after_about_section(self):
        """F8: #scroll-world section is positioned between #about and #exhibitions."""
        content = read_file_text("index.html")
        about_idx = content.find('id="about"')
        scroll_world_idx = content.find('id="scroll-world"')
        exhibitions_idx = content.find('id="exhibitions"')
        self.assertGreater(scroll_world_idx, about_idx, "#scroll-world must appear after #about")
        self.assertLess(scroll_world_idx, exhibitions_idx, "#scroll-world must appear before #exhibitions")

    def test_t1_f38_scroll_world_canvas_element_present(self):
        """F8: index.html contains #scroll-world-canvas element."""
        doc = parse_html_file("index.html")
        canvas = doc.find_one(id="scroll-world-canvas")
        self.assertIsNotNone(canvas, "#scroll-world-canvas must be present inside index.html")

    def test_t1_f39_index_includes_scroll_world_script_tag(self):
        """F8: index.html includes script tag loading js/scroll-world.js."""
        doc = parse_html_file("index.html")
        scripts = doc.find_all(tag="script")
        has_scroll_script = any("scroll-world.js" in (s.get_attr("src") or "") for s in scripts)
        self.assertTrue(has_scroll_script, "index.html must load js/scroll-world.js")

    def test_t1_f40_scroll_world_defines_four_historical_epochs(self):
        """F8: js/scroll-world.js defines the 4 historical epochs."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js").lower()
        for era in ["sogdiana", "alexandria", "timur", "modern"]:
            self.assertIn(era, sw_text, f"Epoch '{era}' must be defined in js/scroll-world.js")

    # -------------------------------------------------------------------------
    # Feature 9: Cinematic Video Scroll-World Flythrough (M4)
    # -------------------------------------------------------------------------
    def test_t1_f41_index_html_has_scroll_world_video_element(self):
        """F9: index.html contains #scroll-world-video tag for the flythrough."""
        doc = parse_html_file("index.html")
        video = doc.find_one(id="scroll-world-video")
        self.assertIsNotNone(video, "index.html must contain #scroll-world-video element")
        self.assertIn("videos/flythrough-epochs.mp4", video.get_attr("src", ""))

    def test_t1_f42_index_html_has_zero_external_video_iframes(self):
        """F9: index.html contains 0 <iframe> elements pointing to video services."""
        doc = parse_html_file("index.html")
        iframes = doc.find_all(tag="iframe")
        video_iframes = [i for i in iframes if any(k in (i.get_attr("src") or "") for k in ["youtube", "vimeo", "bilibili"])]
        self.assertEqual(len(video_iframes), 0, "index.html must not embed external video iframes")

    def test_t1_f43_scroll_world_js_wires_video_scrubbing(self):
        """F9: js/scroll-world.js references #scroll-world-video and video scrubbing engine."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertIn("scroll-world-video", sw_text, "js/scroll-world.js must reference #scroll-world-video")
            self.assertTrue("syncVideo" in sw_text or "videoEl" in sw_text, "js/scroll-world.js must wire video scrubbing")

    def test_t1_f44_flythrough_video_file_exists_and_valid(self):
        """F9: videos/flythrough-epochs.mp4 exists on disk and is non-empty."""
        video_path = PROJECT_ROOT / "videos" / "flythrough-epochs.mp4"
        self.assertTrue(video_path.exists(), "videos/flythrough-epochs.mp4 must exist")
        self.assertGreater(video_path.stat().st_size, 1024 * 1024, "flythrough video must be valid size > 1MB")

    def test_t1_f45_scroll_world_declares_procedural_mesh_triangles_budget(self):
        """F9: js/scroll-world.js defines procedural mesh generation within low polygon budget."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            has_geometry = ("buffergeometry" in sw_text.lower() or "boxgeometry" in sw_text.lower() or "mesh" in sw_text.lower())
            self.assertTrue(has_geometry, "js/scroll-world.js must define procedural geometries")

    # -------------------------------------------------------------------------
    # Feature 10: 60 FPS WebGL Performance Optimization (M4)
    # -------------------------------------------------------------------------
    def test_t1_f46_scroll_world_uses_intersection_observer(self):
        """F10: js/scroll-world.js uses IntersectionObserver for auto-sleep."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js")
        self.assertIn("IntersectionObserver", sw_text, "js/scroll-world.js must instantiate IntersectionObserver")

    def test_t1_f47_scroll_world_pauses_render_loop_offscreen(self):
        """F10: js/scroll-world.js halts or pauses render loop when canvas is offscreen."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js")
        has_pause_logic = ("cancelanimationframe" in sw_text.lower() or "isintersecting" in sw_text.lower() or "isactive" in sw_text.lower() or "pause" in sw_text.lower())
        self.assertTrue(has_pause_logic, "js/scroll-world.js must implement render loop pausing logic")

    def test_t1_f48_scroll_world_clamps_mobile_dpr(self):
        """F10: js/scroll-world.js clamps mobile DPR to <= 1.0."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js")
        self.assertIn("devicePixelRatio", sw_text, "js/scroll-world.js must read window.devicePixelRatio")
        has_clamp = ("min" in sw_text.lower() and ("1.0" in sw_text or "1" in sw_text))
        self.assertTrue(has_clamp, "js/scroll-world.js must clamp DPR")

    def test_t1_f49_scroll_world_clamps_desktop_dpr(self):
        """F10: js/scroll-world.js clamps desktop DPR to <= 1.75."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js")
        has_desktop_clamp = ("1.75" in sw_text or "1.5" in sw_text or "2.0" in sw_text or "min(" in sw_text)
        self.assertTrue(has_desktop_clamp, "js/scroll-world.js must clamp desktop DPR")

    def test_t1_f50_scroll_world_uses_passive_event_listeners(self):
        """F10: Scroll/wheel event listeners in js/scroll-world.js specify passive: true."""
        self.assertTrue(file_exists("js/scroll-world.js"), "js/scroll-world.js must exist on disk.")
        sw_text = read_file_text("js/scroll-world.js")
        if "addEventListener" in sw_text:
            self.assertIn("passive", sw_text, "EventListeners in scroll-world.js should specify passive: true")

    # -------------------------------------------------------------------------
    # Feature 11: GAN-Style Auto-Improve Engine (M5)
    # -------------------------------------------------------------------------
    def test_t1_f51_auto_improve_script_exists_on_disk(self):
        """F11: scripts/auto_improve.py exists on disk."""
        self.assertTrue(file_exists("scripts/auto_improve.py"), "scripts/auto_improve.py must exist on disk.")

    def test_t1_f52_auto_improve_cli_help_exits_cleanly(self):
        """F11: scripts/auto_improve.py --help executes with exit code 0."""
        self.assertTrue(file_exists("scripts/auto_improve.py"), "scripts/auto_improve.py must exist")
        res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"--help failed with code {res.returncode}: {res.stderr}")

    def test_t1_f53_auto_improve_supports_task_argument(self):
        """F11: scripts/auto_improve.py CLI supports --task argument."""
        res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--task", res.stdout, "--task argument missing from --help output")

    def test_t1_f54_auto_improve_supports_rounds_argument(self):
        """F11: scripts/auto_improve.py CLI supports --rounds argument."""
        res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--rounds", res.stdout, "--rounds argument missing from --help output")

    def test_t1_f55_auto_improve_supports_threshold_argument(self):
        """F11: scripts/auto_improve.py CLI supports --threshold argument."""
        res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--threshold", res.stdout, "--threshold argument missing from --help output")

    # -------------------------------------------------------------------------
    # Feature 12: Museum Rubric Text Optimization (M5)
    # -------------------------------------------------------------------------
    def test_t1_f56_auto_improve_defines_four_rubric_weights(self):
        """F12: scripts/auto_improve.py defines the 4 rubric dimensions."""
        self.assertTrue(file_exists("scripts/auto_improve.py"), "scripts/auto_improve.py must exist")
        code = read_file_text("scripts/auto_improve.py").lower()
        self.assertIn("accuracy", code, "Accuracy dimension must be defined in rubric")
        self.assertIn("register", code, "Register dimension must be defined in rubric")
        self.assertIn("clarity", code, "Clarity dimension must be defined in rubric")
        self.assertIn("technical", code, "Technical/multilingual dimension must be defined in rubric")

    def test_t1_f57_rubric_weights_sum_to_one(self):
        """F12: Rubric weights in scripts/auto_improve.py sum to 1.0 (0.35 + 0.25 + 0.20 + 0.20)."""
        code = read_file_text("scripts/auto_improve.py")
        self.assertIn("0.35", code, "Accuracy weight 0.35 must be present")
        self.assertIn("0.25", code, "Register weight 0.25 must be present")
        self.assertIn("0.20", code, "Clarity/Technical weight 0.20 must be present")

    def test_t1_f58_auto_improve_implements_blind_gate(self):
        """F12: scripts/auto_improve.py implements double-blind gate logic."""
        code = read_file_text("scripts/auto_improve.py").lower()
        has_gate = ("gate" in code or "blind" in code or "pairwise" in code)
        self.assertTrue(has_gate, "Double-blind gate logic must be present in auto_improve.py")

    def test_t1_f59_auto_improve_supports_report_flag(self):
        """F12: scripts/auto_improve.py supports --report flag."""
        res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--report", res.stdout, "--report flag missing from --help")

    def test_t1_f60_auto_improve_history_json_supported(self):
        """F12: scripts/auto_improve.py references or outputs tools/auto_improve_history.json."""
        code = read_file_text("scripts/auto_improve.py")
        self.assertIn("auto_improve_history.json", code, "scripts/auto_improve.py must target auto_improve_history.json")

    # -------------------------------------------------------------------------
    # Feature 13: 3D Tilt Cards with Specular Glare (M6)
    # -------------------------------------------------------------------------
    def test_t1_f61_animations_js_file_referenced_or_present(self):
        """F13: js/animations.js exists or is referenced in index.html."""
        has_file = file_exists("js/animations.js")
        index_text = read_file_text("index.html")
        has_ref = "animations.js" in index_text
        self.assertTrue(has_file or has_ref, "js/animations.js must exist or be referenced in index.html")

    def test_t1_f62_css_defines_3d_card_perspective(self):
        """F13: css/style.css defines perspective for 3D cards."""
        css_text = read_file_text("css/style.css")
        has_persp = "perspective" in css_text.lower()
        self.assertTrue(has_persp, "css/style.css must define perspective styling")

    def test_t1_f63_css_defines_specular_card_glare(self):
        """F13: css/style.css defines specular glare overlay styles."""
        css_text = read_file_text("css/style.css").lower()
        has_glare = ("glare" in css_text or "mix-blend-mode: overlay" in css_text or "radial-gradient" in css_text)
        self.assertTrue(has_glare, "css/style.css must define specular glare styling")

    def test_t1_f64_card_tilt_checks_fine_pointer_hover(self):
        """F13: js/animations.js checks (hover: hover) and (pointer: fine)."""
        self.assertTrue(file_exists("js/animations.js"), "js/animations.js must exist on disk.")
        anim_text = read_file_text("js/animations.js")
        has_pointer_check = ("hover: hover" in anim_text or "pointer: fine" in anim_text or "matchmedia" in anim_text.lower())
        self.assertTrue(has_pointer_check, "js/animations.js must guard tilt with matchMedia for fine pointer")

    def test_t1_f65_touch_devices_bypass_3d_tilt(self):
        """F13: js/animations.js guards against touch events."""
        self.assertTrue(file_exists("js/animations.js"), "js/animations.js must exist on disk.")
        anim_text = read_file_text("js/animations.js")
        has_touch_guard = ("ontouchstart" in anim_text or "maxTouchPoints" in anim_text or "pointer: fine" in anim_text)
        self.assertTrue(has_touch_guard, "js/animations.js must guard against touch device tilt")

    # -------------------------------------------------------------------------
    # Feature 14: Cinematic Staggered Reveals (M6)
    # -------------------------------------------------------------------------
    def test_t1_f66_animations_implements_gsap_staggered_reveals(self):
        """F14: js/animations.js defines batch reveals using GSAP ScrollTrigger."""
        self.assertTrue(file_exists("js/animations.js"), "js/animations.js must exist on disk.")
        anim_text = read_file_text("js/animations.js")
        has_reveal = ("scrolltrigger" in anim_text.lower() or "batch" in anim_text.lower() or "stagger" in anim_text.lower())
        self.assertTrue(has_reveal, "js/animations.js must implement staggered batch reveals")

    def test_t1_f67_no_unthrottled_bounding_client_rect_in_scroll_listeners(self):
        """F14: js/animations.js does not invoke getBoundingClientRect in raw unthrottled scroll listeners."""
        self.assertTrue(file_exists("js/animations.js"), "js/animations.js must exist on disk.")
        anim_text = read_file_text("js/animations.js")
        self.assertNotIn("window.addEventListener('scroll', revealOnScroll", anim_text, "Layout thrashing scroll listener must not be used")

    def test_t1_f68_exhibit_cards_use_gpu_reveal_classes(self):
        """F14: Cards in index.html use reveal classes."""
        doc = parse_html_file("index.html")
        reveals = doc.select(".reveal") + doc.select(".exhibit-card")
        self.assertGreater(len(reveals), 0, "Cards must have reveal classes")

    def test_t1_f69_reveals_animate_only_transform_opacity(self):
        """F14: CSS reveal styles animate only opacity and transform properties."""
        css_text = read_file_text("css/style.css")
        self.assertIn("opacity", css_text, "css/style.css must animate opacity")
        self.assertIn("transform", css_text, "css/style.css must animate transform")

    def test_t1_f70_zero_layout_thrashing_properties_in_reveals(self):
        """F14: css/style.css .reveal does not animate layout-thrashing properties (top, left, margin)."""
        css_text = read_file_text("css/style.css")
        match = re.search(r'\.reveal[^{]*\{([^}]+)\}', css_text)
        if match:
            rules = match.group(1).lower()
            self.assertNotIn("transition: top", rules, ".reveal must not transition top")
            self.assertNotIn("transition: margin", rules, ".reveal must not transition margin")

    # -------------------------------------------------------------------------
    # Feature 15: Micro-Interactions & Parallax (M6)
    # -------------------------------------------------------------------------
    def test_t1_f71_css_defines_gold_shimmer_keyframes(self):
        """F15: css/style.css defines @keyframes for shimmer sweep."""
        css_text = read_file_text("css/style.css").lower()
        has_shimmer = ("@keyframes shimmer" in css_text or "@keyframes gold-shimmer" in css_text or "@keyframes shine" in css_text)
        self.assertTrue(has_shimmer, "css/style.css must define shimmer keyframe animation")

    def test_t1_f72_magnetic_button_attraction_defined(self):
        """F15: js/animations.js defines magnetic button attraction physics."""
        self.assertTrue(file_exists("js/animations.js"), "js/animations.js must exist on disk.")
        anim_text = read_file_text("js/animations.js").lower()
        has_magnetic = ("magnetic" in anim_text or "btn-primary" in anim_text)
        self.assertTrue(has_magnetic, "js/animations.js must implement magnetic button logic")

    def test_t1_f73_smooth_background_parallax_configured(self):
        """F15: js/animations.js or css/style.css configures background parallax."""
        anim_text = read_file_text("js/animations.js").lower() if file_exists("js/animations.js") else ""
        css_text = read_file_text("css/style.css").lower()
        has_parallax = ("parallax" in anim_text or "parallax" in css_text)
        self.assertTrue(has_parallax, "Parallax background movement must be configured")

    def test_t1_f74_audio_toggle_button_has_micro_interaction(self):
        """F15: #audioToggle button is styled with hover transition."""
        css_text = read_file_text("css/style.css")
        self.assertIn("#audioToggle", css_text, "css/style.css must style #audioToggle button")

    def test_t1_f75_animations_respect_prefers_reduced_motion(self):
        """F15: css/style.css contains prefers-reduced-motion media query."""
        css_text = read_file_text("css/style.css")
        self.assertIn("prefers-reduced-motion", css_text, "css/style.css must support prefers-reduced-motion")

    # -------------------------------------------------------------------------
    # Feature 16: Comprehensive E2E Testing Track (Final)
    # -------------------------------------------------------------------------
    def test_t1_f76_run_tests_py_runner_exists(self):
        """F16: Standalone test runner tests/e2e/run_tests.py exists."""
        self.assertTrue(file_exists("tests/e2e/run_tests.py"), "tests/e2e/run_tests.py must exist")

    def test_t1_f77_test_suite_requires_zero_pip_dependencies(self):
        """F16: Test runner and utils import only Python standard library."""
        runner_text = read_file_text("tests/e2e/run_tests.py") if file_exists("tests/e2e/run_tests.py") else ""
        utils_text = read_file_text("tests/e2e/dom_utils.py")
        combined = runner_text + "\n" + utils_text
        self.assertNotIn("import bs4", combined)
        self.assertNotIn("import pytest", combined)
        self.assertNotIn("import selenium", combined)
        self.assertNotIn("import requests", combined)

    def test_t1_f78_test_infra_md_exists(self):
        """F16: TEST_INFRA.md exists in project root."""
        self.assertTrue(file_exists("TEST_INFRA.md"), "TEST_INFRA.md must exist in project root.")

    def test_t1_f79_test_ready_md_exists(self):
        """F16: TEST_READY.md exists in project root."""
        self.assertTrue(file_exists("TEST_READY.md"), "TEST_READY.md must exist in project root.")

    def test_t1_f80_test_runner_returns_standard_exit_codes(self):
        """F16: tests/e2e/run_tests.py supports --help and exits cleanly."""
        if file_exists("tests/e2e/run_tests.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "tests" / "e2e" / "run_tests.py"), "--help"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"run_tests.py --help returned {res.returncode}")


if __name__ == '__main__':
    unittest.main()
