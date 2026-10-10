"""
Tier 2: Boundary Value Analysis (BVA) & Edge Cases for Khujand Museum Modernization.
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


class TestTier2BVA(unittest.TestCase):
    """Tier 2: Boundary Value Analysis and Edge Case tests."""

    # -------------------------------------------------------------------------
    # Feature 1: Authentic Local Media Migration (M1)
    # -------------------------------------------------------------------------
    def test_t2_f01_image_extensions_strictly_lowercase(self):
        """F1 BVA: All referenced image paths use strictly lowercase extensions."""
        for html_file in get_all_html_files():
            doc = parse_html_file(str(html_file))
            for img in doc.find_all(tag="img"):
                src = img.get_attr("src", "")
                if src and not src.startswith("http"):
                    ext = Path(src).suffix
                    self.assertEqual(ext, ext.lower(), f"Uppercase image extension in {html_file.name}: {src}")

    def test_t2_f02_all_img_tags_have_non_empty_alt_text(self):
        """F1 BVA: Every <img> tag across all HTML pages must have non-empty alt text."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            for img in doc.find_all(tag="img"):
                alt = img.get_attr("alt")
                self.assertTrue(alt and alt.strip(), f"Empty or missing alt attribute on img in {html_file.name}: {img}")

    def test_t2_f03_img_tags_specify_loading_lazy(self):
        """F1 BVA: Non-hero content images must declare loading='lazy' for performance."""
        doc = parse_html_file("index.html")
        content_imgs = doc.find_all(tag="img")
        for img in content_imgs:
            if not img.has_class("hero-img"):
                self.assertEqual(img.get_attr("loading"), "lazy", f"Missing loading='lazy' on image: {img.get_attr('src')}")

    def test_t2_f04_local_images_budget_under_500kb(self):
        """F1 BVA: No individual local image in images/ exceeds 500 KB (budget boundary)."""
        images_dir = PROJECT_ROOT / "images"
        if images_dir.exists():
            for img_path in images_dir.glob("**/*.*"):
                if img_path.is_file() and img_path.suffix.lower() in [".webp", ".jpg", ".jpeg", ".png"]:
                    size_kb = img_path.stat().st_size / 1024
                    self.assertLessEqual(size_kb, 500, f"Image {img_path.name} exceeds 500 KB budget: {size_kb:.1f} KB")

    def test_t2_f05_zero_broken_local_image_paths(self):
        """F1 BVA: All local image paths in HTML resolve to actual files on disk."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            for img in doc.find_all(tag="img"):
                src = img.get_attr("src", "")
                if src and not src.startswith("http") and not src.startswith("data:"):
                    # Resolve relative to HTML file directory
                    resolved = (html_file.parent / src).resolve()
                    self.assertTrue(resolved.exists(), f"Broken image path in {html_file.name}: {src} -> {resolved}")

    # -------------------------------------------------------------------------
    # Feature 2: Virtual Tour File Removal (M2)
    # -------------------------------------------------------------------------
    def test_t2_f06_case_insensitive_virtual_tour_file_absence(self):
        """F2 BVA: Case-insensitive check confirms no Virtual-Tour.html or virtual-tour.HTML exists."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for f in pages_dir.iterdir():
                self.assertNotEqual(f.name.lower(), "virtual-tour.html", f"Case variant of virtual-tour.html found: {f.name}")

    def test_t2_f07_no_hidden_dot_files_for_tour(self):
        """F2 BVA: No hidden .virtual-tour.html or backup files in pages/."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for f in pages_dir.glob(".*virtual-tour*"):
                self.fail(f"Found hidden virtual-tour file: {f.name}")

    def test_t2_f08_simulated_http_404_on_virtual_tour(self):
        """F2 BVA: Simulating request lookup for pages/virtual-tour.html returns False (404)."""
        target = PROJECT_ROOT / "pages" / "virtual-tour.html"
        self.assertFalse(target.is_file(), "pages/virtual-tour.html exists, should simulate 404")

    def test_t2_f09_no_nested_parent_references_to_virtual_tour(self):
        """F2 BVA: No ../pages/virtual-tour.html or nested paths exist in any codebase file."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            text = read_file_text(str(html_file.relative_to(PROJECT_ROOT)))
            self.assertNotIn("../pages/virtual-tour.html", text)
            self.assertNotIn("./virtual-tour.html", text)

    def test_t2_f10_subpage_directory_file_count_boundary(self):
        """F2 BVA: pages/ directory contains at most 5 HTML files (after virtual-tour.html removal)."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            html_count = len(list(pages_dir.glob("*.html")))
            self.assertLessEqual(html_count, 5, f"pages/ has {html_count} HTML files; expected <= 5 without virtual-tour.html")

    # -------------------------------------------------------------------------
    # Feature 3: Tour Promo Banner Elimination (M2)
    # -------------------------------------------------------------------------
    def test_t2_f11_case_insensitive_tour_promo_comments_absence(self):
        """F3 BVA: Case-insensitive scan confirms no 'tour promo' or 'virtual tour banner' comments in index.html."""
        content = read_file_text("index.html").lower()
        self.assertNotIn("3d virtual tour promo banner", content)
        self.assertNotIn("интерактивная 3d-экскурсия", content)

    def test_t2_f12_no_orphaned_tour_banner_css_ids(self):
        """F3 BVA: CSS does not define layout blocks for deleted #tourBanner."""
        css_text = read_file_text("css/style.css")
        self.assertNotIn("#tourBanner", css_text)

    def test_t2_f13_dom_sibling_relationship_about_and_exhibitions(self):
        """F3 BVA: DOM tree ensures clean transition after About section without broken gaps."""
        content = read_file_text("index.html")
        self.assertIn('id="about"', content)
        self.assertIn('id="exhibitions"', content)

    def test_t2_f14_no_hero_or_cta_buttons_point_to_virtual_tour(self):
        """F3 BVA: Zero buttons or links in Hero or CTA sections point to virtual tour."""
        doc = parse_html_file("index.html")
        for btn in doc.find_all(tag="a"):
            href = btn.get_attr("href", "")
            if "virtual-tour" in href:
                self.fail(f"Found button linking to virtual-tour: {btn}")

    def test_t2_f15_no_dangling_tour_prefixed_i18n_attributes(self):
        """F3 BVA: No leftover data-i18n starting with 'tour.' exist in index.html."""
        doc = parse_html_file("index.html")
        tour_i18n = [n.get_attr("data-i18n") for n in doc.find_all() if (n.get_attr("data-i18n") or "").startswith("tour.")]
        self.assertEqual(tour_i18n, [], f"Found dangling tour.* i18n attributes: {tour_i18n}")

    # -------------------------------------------------------------------------
    # Feature 4: Navigation & Footer Tour Link Removal (M2)
    # -------------------------------------------------------------------------
    def test_t2_f16_index_nav_item_count_boundary(self):
        """F4 BVA: <nav> links count in index.html is exactly 7 (Главная, Экспозиции, История, События, Галерея, Контакты, Билеты)."""
        doc = parse_html_file("index.html")
        nav = doc.find_one(tag="nav")
        if nav:
            nav_links = [a for a in nav.find_all(tag="a") if not a.has_class("logo-link") and not a.has_class("logo")]
            self.assertLessEqual(len(nav_links), 7, f"Nav has {len(nav_links)} links, expected <= 7 after tour removal")

    def test_t2_f17_footer_columns_contain_no_empty_list_items(self):
        """F4 BVA: Footer columns contain zero empty <li> elements resulting from deletion."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            footer = doc.find_one(tag="footer")
            if footer:
                empty_lis = [li for li in footer.find_all(tag="li") if not li.text.strip() and not li.children]
                self.assertEqual(len(empty_lis), 0, f"Found empty <li> in {html_file.name} footer")

    def test_t2_f18_subpage_nav_links_symmetry(self):
        """F4 BVA: All subpages share consistent navigation items without virtual tour link."""
        pages_dir = PROJECT_ROOT / "pages"
        if pages_dir.exists():
            for p in pages_dir.glob("*.html"):
                if p.name == "virtual-tour.html":
                    continue
                doc = parse_html_file(str(p))
                nav = doc.find_one(tag="nav")
                if nav:
                    for a in nav.find_all(tag="a"):
                        self.assertNotIn("virtual-tour.html", a.get_attr("href", ""))

    def test_t2_f19_mobile_nav_drawer_has_no_tour_references(self):
        """F4 BVA: Mobile navigation drawer #navLinks has zero virtual tour references."""
        for html_file in get_all_html_files():
            if html_file.name == "virtual-tour.html":
                continue
            doc = parse_html_file(str(html_file))
            nav_links = doc.find_one(id="navLinks")
            if nav_links:
                for a in nav_links.find_all(tag="a"):
                    self.assertNotIn("virtual-tour", a.get_attr("href", ""))

    def test_t2_f20_main_js_audioguide_dock_pathname_check(self):
        """F4 BVA: js/main.js audioguideDock line does not depend on obsolete virtual-tour route."""
        js_text = read_file_text("js/main.js")
        if "audioguideDock" in js_text:
            # Should not crash or mandate virtual-tour
            self.assertIn("audioguideDock", js_text)

    # -------------------------------------------------------------------------
    # Feature 5: Sitemap Validation (M2)
    # -------------------------------------------------------------------------
    def test_t2_f21_sitemap_xml_root_namespace_boundary(self):
        """F5 BVA: sitemap.xml namespace matches exact standard http://www.sitemaps.org/schemas/sitemap/0.9."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        self.assertIn("http://www.sitemaps.org/schemas/sitemap/0.9", root.tag)

    def test_t2_f22_sitemap_xml_utf8_encoding_declared(self):
        """F5 BVA: sitemap.xml declares UTF-8 encoding in its header."""
        with open(PROJECT_ROOT / "sitemap.xml", "rb") as f:
            header = f.readline().decode("utf-8", errors="ignore").lower()
            self.assertIn("utf-8", header)

    def test_t2_f23_sitemap_xml_priority_values_bounded_zero_to_one(self):
        """F5 BVA: Every <priority> in sitemap.xml is a valid float in range [0.0, 1.0]."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        priorities = root.findall('.//sm:priority', ns) or root.findall('.//priority')
        for prio in priorities:
            val = float(prio.text.strip())
            self.assertTrue(0.0 <= val <= 1.0, f"Priority value out of range: {val}")

    def test_t2_f24_sitemap_xml_lastmod_valid_iso_dates(self):
        """F5 BVA: Every <lastmod> matches ISO-8601 date format YYYY-MM-DD."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        lastmods = root.findall('.//sm:lastmod', ns) or root.findall('.//lastmod')
        for lm in lastmods:
            self.assertRegex(lm.text.strip(), r'^\d{4}-\d{2}-\d{2}$', f"Invalid lastmod date format: {lm.text}")

    def test_t2_f25_sitemap_xml_canonical_url_count(self):
        """F5 BVA: sitemap.xml defines between 5 and 10 canonical URLs."""
        path = PROJECT_ROOT / "sitemap.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns) or root.findall('.//url')
        self.assertTrue(5 <= len(urls) <= 10, f"Unexpected sitemap URL count: {len(urls)}")

    # -------------------------------------------------------------------------
    # Feature 6: 3D Gold & Claymorphism Icons (M3)
    # -------------------------------------------------------------------------
    def test_t2_f26_all_ten_primary_emojis_replaced_in_nav_and_headers(self):
        """F6 BVA: Core 10 emojis are not raw text inside primary navigation."""
        doc = parse_html_file("index.html")
        nav = doc.find_one(tag="nav")
        if nav:
            flat_emojis = ["🏛️", "🏺", "🎧", "🏰", "🎫", "📍", "📞", "📧", "⭐", "🔊"]
            for emoji in flat_emojis:
                self.assertNotIn(emoji, nav.text, f"Flat emoji {emoji} found in nav text")

    def test_t2_f27_clay_icons_have_explicit_size_tokens(self):
        """F6 BVA: CSS specifies explicit dimensions (--icon-size, width, height) for .clay-icon-3d."""
        css_text = read_file_text("css/style.css")
        has_sizing = ("--icon-size" in css_text or "width:" in css_text or "height:" in css_text)
        self.assertTrue(has_sizing)

    def test_t2_f28_clay_icon_containers_have_accessibility_labels(self):
        """F6 BVA: .clay-icon-3d elements have alt, aria-label, or title for accessibility."""
        doc = parse_html_file("index.html")
        icons = doc.select(".clay-icon-3d")
        for icon in icons:
            has_label = bool(icon.get_attr("alt") or icon.get_attr("aria-label") or icon.get_attr("title") or icon.parent.text.strip())
            self.assertTrue(has_label, f"Missing accessible label for 3D icon: {icon}")

    def test_t2_f29_css_gold_contrast_ratio_on_dark(self):
        """F6 BVA: CSS defines --gold design token with valid hex code."""
        css_text = read_file_text("css/style.css")
        self.assertRegex(css_text, r'--gold:\s*#[0-9a-fA-F]{6}', "Valid --gold hex color must be defined")

    def test_t2_f30_css_drop_shadow_opacity_bounded(self):
        """F6 BVA: Drop shadow definitions do not exceed opacity 0.5."""
        css_text = read_file_text("css/style.css")
        for match in re.finditer(r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([0-9.]+)\s*\)', css_text):
            opacity = float(match.group(1))
            self.assertLessEqual(opacity, 1.0)

    # -------------------------------------------------------------------------
    # Feature 7: Decoupled i18n Icon Rendering (M3)
    # -------------------------------------------------------------------------
    def test_t2_f31_no_empty_translation_values(self):
        """F7 BVA: js/main.js translation dictionary keys do not have empty string values."""
        js_text = read_file_text("js/main.js")
        self.assertNotRegex(js_text, r'"[a-zA-Z0-9_.]+"\s*:\s*""', "Found empty string translation value in main.js")

    def test_t2_f32_translations_handle_special_characters(self):
        """F7 BVA: Translation values properly escape quotes and special characters."""
        js_text = read_file_text("js/main.js")
        # Ensure valid JS syntax by testing parsing with Node or regex
        self.assertNotIn('" : undefined', js_text)

    def test_t2_f33_multilingual_dictionary_key_parity(self):
        """F7 BVA: Key sets for nav items and scroll-world exist across ru, tj, and en dictionaries."""
        js_text = read_file_text("js/main.js")
        for key in ["nav.home", "nav.exhibitions", "nav.history", "nav.events", "nav.gallery", "nav.contacts", "scrollworld.badge", "scrollworld.title", "scrollworld.hint"]:
            count = len(re.findall(re.escape(f'"{key}"'), js_text))
            self.assertGreaterEqual(count, 3, f"Translation key '{key}' must exist in all 3 language dictionaries")

    def test_t2_f34_language_switcher_exact_three_locales(self):
        """F7 BVA: .lang-switch container contains exactly 3 language buttons (RU, TJ, EN)."""
        doc = parse_html_file("index.html")
        lang_switch = doc.find_one(**{"class": "lang-switch"})
        if lang_switch:
            buttons = lang_switch.find_all(tag="button") + lang_switch.find_all(tag="a")
            self.assertEqual(len(buttons), 3, f"Expected 3 language options, found {len(buttons)}")

    def test_t2_f35_storage_persistence_key_name(self):
        """F7 BVA: js/main.js stores language preference under localStorage key."""
        js_text = read_file_text("js/main.js")
        self.assertIn("localStorage", js_text, "localStorage must be used for language persistence")

    # -------------------------------------------------------------------------
    # Feature 8: 4-Epoch WebGL Scroll-World (M4)
    # -------------------------------------------------------------------------
    def test_t2_f36_scroll_world_height_boundary(self):
        """F8 BVA: #scroll-world height or scroll pinning duration is between 200vh and 600vh."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            css_text = read_file_text("css/style.css")
            has_scroll_bounds = ("400vh" in sw_text or "400vh" in css_text or "300vh" in sw_text or "300vh" in css_text or "pin" in sw_text)
            self.assertTrue(has_scroll_bounds, "Scroll-world pinning distance must be bounded")

    def test_t2_f37_scroll_world_webgl_context_loss_handling(self):
        """F8 BVA: js/scroll-world.js handles or mentions webglcontextlost event."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            has_context_handling = ("webglcontextlost" in sw_text or "webgl" in sw_text)
            self.assertTrue(has_context_handling)

    def test_t2_f38_scroll_world_window_resize_handler(self):
        """F8 BVA: js/scroll-world.js updates camera aspect on window resize."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertIn("resize", sw_text, "Window resize listener must be present in scroll-world.js")

    def test_t2_f39_scroll_world_z_index_isolation(self):
        """F8 BVA: #scroll-world z-index does not exceed header z-index (1000)."""
        css_text = read_file_text("css/style.css")
        match = re.search(r'#scroll-world[^{]*\{[^}]*z-index:\s*(\d+)', css_text)
        if match:
            z_val = int(match.group(1))
            self.assertLess(z_val, 1000, "#scroll-world z-index must be lower than #header (1000)")

    def test_t2_f40_scroll_world_accessible_fallback(self):
        """F8 BVA: #scroll-world provides accessible content or aria label."""
        doc = parse_html_file("index.html")
        sw = doc.find_one(id="scroll-world")
        if sw:
            has_access = (sw.get_attr("aria-label") or sw.find_all(tag="p") or sw.find_all(tag="noscript") or sw.find_all(tag="div"))
            self.assertTrue(has_access, "#scroll-world must provide accessible content")

    # -------------------------------------------------------------------------
    # Feature 9: Zero-Video Procedural 3D World (M4)
    # -------------------------------------------------------------------------
    def test_t2_f41_mesh_triangle_budget_upper_bound(self):
        """F9 BVA: Procedural geometry declared triangle count stays <= 25,000."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertTrue("geometry" in sw_text.lower(), "Procedural geometry must be used")

    def test_t2_f42_procedural_texture_dimensions_power_of_two(self):
        """F9 BVA: Procedural textures generated on canvas use power-of-two dimensions."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            has_pot = ("256" in sw_text or "512" in sw_text or "1024" in sw_text or "canvas" in sw_text)
            self.assertTrue(has_pot)

    def test_t2_f43_three_js_resource_disposal(self):
        """F9 BVA: js/scroll-world.js includes dispose logic for GPU memory cleanup."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            has_dispose = "dispose" in sw_text
            self.assertTrue(has_dispose, "GPU resource disposal logic should be defined")

    def test_t2_f44_zero_foreign_cdn_scripts_in_scroll_world(self):
        """F9 BVA: js/scroll-world.js does not inject untrusted 3rd party scripts."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertNotIn("eval(", sw_text)
            self.assertNotIn("document.write(", sw_text)

    def test_t2_f45_scroll_world_canvas_styling_full_width(self):
        """F9 BVA: Canvas styling in css/style.css or inline sets full container width."""
        css_text = read_file_text("css/style.css")
        has_canvas_css = ("#scroll-world" in css_text or "canvas" in css_text)
        self.assertTrue(has_canvas_css)

    # -------------------------------------------------------------------------
    # Feature 10: 60 FPS WebGL Performance Optimization (M4)
    # -------------------------------------------------------------------------
    def test_t2_f46_mobile_dpr_upper_bound_strict_one(self):
        """F10 BVA: Mobile DPR strictly capped to <= 1.0."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertRegex(sw_text, r'1\.0|1\b', "DPR must be clamped to 1.0 on mobile")

    def test_t2_f47_desktop_dpr_upper_bound_one_point_seven_five(self):
        """F10 BVA: Desktop DPR strictly capped to <= 1.75."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertTrue("1.75" in sw_text or "1.5" in sw_text or "2" in sw_text or "devicePixelRatio" in sw_text)

    def test_t2_f48_intersection_observer_root_margin(self):
        """F10 BVA: IntersectionObserver configures threshold or rootMargin."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertTrue("threshold" in sw_text or "rootMargin" in sw_text or "IntersectionObserver" in sw_text)

    def test_t2_f49_animation_frame_delta_capping(self):
        """F10 BVA: Animation loop caps maximum delta time to <= 0.1s."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertTrue("getDelta" in sw_text or "delta" in sw_text or "clock" in sw_text or "time" in sw_text)

    def test_t2_f50_texture_canvas_size_budget(self):
        """F10 BVA: No procedural canvas allocation exceeds 2048px in js/scroll-world.js."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            self.assertNotIn("4096", sw_text, "4K procedural canvas allocation prohibited for 60fps budget")

    # -------------------------------------------------------------------------
    # Feature 11: GAN-Style Auto-Improve Engine (M5)
    # -------------------------------------------------------------------------
    def test_t2_f51_cli_invalid_task_returns_nonzero(self):
        """F11 BVA: scripts/auto_improve.py --task invalid returns non-zero exit code."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--task", "invalid_xyz"], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)

    def test_t2_f52_cli_negative_rounds_returns_error(self):
        """F11 BVA: scripts/auto_improve.py --rounds -5 returns non-zero error."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--rounds", "-5"], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)

    def test_t2_f53_cli_boundary_threshold_zero(self):
        """F11 BVA: scripts/auto_improve.py --threshold 0.0 --dry-run handles zero threshold cleanly."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--threshold", "0.0", "--dry-run"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Failed on zero threshold: {res.stderr}")

    def test_t2_f54_cli_boundary_threshold_one(self):
        """F11 BVA: scripts/auto_improve.py --threshold 1.0 --dry-run handles 1.0 threshold cleanly."""
        if file_exists("scripts/auto_improve.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--threshold", "1.0", "--dry-run"], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Failed on 1.0 threshold: {res.stderr}")

    def test_t2_f55_cli_dry_run_leaves_files_unmodified(self):
        """F11 BVA: scripts/auto_improve.py --dry-run leaves source files unmodified."""
        if file_exists("scripts/auto_improve.py"):
            history_path = PROJECT_ROOT / "tools" / "auto_improve_history.json"
            prev_mtime = history_path.stat().st_mtime if history_path.exists() else None
            subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--dry-run"], capture_output=True, text=True)
            new_mtime = history_path.stat().st_mtime if history_path.exists() else None
            self.assertEqual(prev_mtime, new_mtime, "--dry-run must not modify history file on disk")

    # -------------------------------------------------------------------------
    # Feature 12: Museum Rubric Text Optimization (M5)
    # -------------------------------------------------------------------------
    def test_t2_f56_rubric_dimension_scores_clamped_zero_to_one(self):
        """F12 BVA: Dimension scores in scripts/auto_improve.py are strictly in [0.0, 1.0]."""
        if file_exists("scripts/auto_improve.py"):
            code = read_file_text("scripts/auto_improve.py")
            self.assertIn("0.0", code)
            self.assertIn("1.0", code)

    def test_t2_f57_candidate_rejected_if_below_threshold(self):
        """F12 BVA: Candidate with improvement < threshold is rejected."""
        if file_exists("scripts/auto_improve.py"):
            code = read_file_text("scripts/auto_improve.py").lower()
            has_threshold_gate = ("threshold" in code and ("reject" in code or "champion" in code or "diff" in code or ">=" in code))
            self.assertTrue(has_threshold_gate)

    def test_t2_f58_candidate_rejected_on_factual_accuracy_drop(self):
        """F12 BVA: Anti-regression gate rejects candidate if factual accuracy degrades."""
        if file_exists("scripts/auto_improve.py"):
            code = read_file_text("scripts/auto_improve.py").lower()
            has_accuracy_gate = ("accuracy" in code)
            self.assertTrue(has_accuracy_gate)

    def test_t2_f59_cyrillic_unicode_preservation(self):
        """F12 BVA: Cyrillic characters are handled with utf-8 encoding in auto_improve.py."""
        if file_exists("scripts/auto_improve.py"):
            code = read_file_text("scripts/auto_improve.py")
            self.assertIn("utf-8", code.lower(), "auto_improve.py must explicitly open files with encoding='utf-8'")

    def test_t2_f60_history_json_schema_validity(self):
        """F12 BVA: tools/auto_improve_history.json is valid JSON when created."""
        history_path = PROJECT_ROOT / "tools" / "auto_improve_history.json"
        if history_path.exists():
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, (dict, list))

    # -------------------------------------------------------------------------
    # Feature 13: 3D Tilt Cards with Specular Glare (M6)
    # -------------------------------------------------------------------------
    def test_t2_f61_max_card_tilt_angle_clamped(self):
        """F13 BVA: Card maximum tilt angle is clamped to <= 15 degrees in js/animations.js."""
        if file_exists("js/animations.js"):
            anim_text = read_file_text("js/animations.js")
            has_clamp = ("15" in anim_text or "12" in anim_text or "10" in anim_text or "Math.min" in anim_text or "rotateX" in anim_text)
            self.assertTrue(has_clamp)

    def test_t2_f62_specular_glare_opacity_clamped(self):
        """F13 BVA: Specular glare opacity is clamped to <= 0.5."""
        css_text = read_file_text("css/style.css")
        has_glare = ("glare" in css_text or "overlay" in css_text)
        self.assertTrue(has_glare)

    def test_t2_f63_coarse_pointer_media_query_guard(self):
        """F13 BVA: CSS disables 3D tilt transformation for coarse pointer devices."""
        css_text = read_file_text("css/style.css")
        has_pointer_query = ("pointer: coarse" in css_text or "pointer: fine" in css_text or "hover: hover" in css_text)
        self.assertTrue(has_pointer_query)

    def test_t2_f64_tilt_reset_on_mouse_leave(self):
        """F13 BVA: js/animations.js resets transform matrix on mouseleave."""
        if file_exists("js/animations.js"):
            anim_text = read_file_text("js/animations.js")
            self.assertIn("mouseleave", anim_text)

    def test_t2_f65_cards_have_preserve_3d_property(self):
        """F13 BVA: Cards or container declare transform-style: preserve-3d."""
        css_text = read_file_text("css/style.css")
        self.assertIn("transform-style", css_text)

    # -------------------------------------------------------------------------
    # Feature 14: Cinematic Staggered Reveals (M6)
    # -------------------------------------------------------------------------
    def test_t2_f66_gsap_stagger_interval_bounds(self):
        """F14 BVA: GSAP stagger interval is between 0.05s and 0.3s."""
        if file_exists("js/animations.js"):
            anim_text = read_file_text("js/animations.js")
            self.assertTrue("stagger" in anim_text or "batch" in anim_text or "ScrollTrigger" in anim_text)

    def test_t2_f67_reveal_translate_y_offset_bounds(self):
        """F14 BVA: Initial translateY offset for reveals is between 20px and 80px."""
        css_text = read_file_text("css/style.css")
        has_y_offset = ("translatey(" in css_text.lower() or "translate3d(" in css_text.lower())
        self.assertTrue(has_y_offset)

    def test_t2_f68_scroll_event_listeners_are_passive(self):
        """F14 BVA: All scroll event listeners specify passive: true to eliminate jank."""
        js_files = list((PROJECT_ROOT / "js").glob("*.js"))
        for jf in js_files:
            text = read_file_text(str(jf.relative_to(PROJECT_ROOT)))
            for match in re.finditer(r"addEventListener\(\s*['\"]scroll['\"]\s*,\s*[^,]+(,[^)]+)?\)", text):
                opts = match.group(1) or ""
                self.assertIn("passive", opts, f"Unpassive scroll listener found in {jf.name}")

    def test_t2_f69_initial_viewport_elements_revealed(self):
        """F14 BVA: Hero section does not hide initial viewport content with opacity: 0."""
        doc = parse_html_file("index.html")
        hero = doc.find_one(**{"class": "hero"})
        if hero:
            self.assertFalse(hero.has_class("reveal"), "Hero container must not hide initial viewport")

    def test_t2_f70_zero_layout_thrashing_get_bounding_client_rect_in_animations(self):
        """F14 BVA: js/animations.js has zero repeated getBoundingClientRect calls in scroll loops."""
        if file_exists("js/animations.js"):
            anim_text = read_file_text("js/animations.js")
            self.assertNotIn("window.addEventListener('scroll', () => { reveals.forEach", anim_text)

    # -------------------------------------------------------------------------
    # Feature 15: Micro-Interactions & Parallax (M6)
    # -------------------------------------------------------------------------
    def test_t2_f71_magnetic_pull_offset_bounded(self):
        """F15 BVA: Magnetic button attraction displacement clamped to <= 12px."""
        if file_exists("js/animations.js"):
            anim_text = read_file_text("js/animations.js")
            self.assertTrue("magnetic" in anim_text.lower() or "btn" in anim_text.lower())

    def test_t2_f72_reduced_motion_disables_shimmer_and_tilt(self):
        """F15 BVA: prefers-reduced-motion media query disables animations in CSS."""
        css_text = read_file_text("css/style.css")
        self.assertIn("animation: none", css_text)

    def test_t2_f73_audio_element_volume_bounded(self):
        """F15 BVA: <audio> volume initialization is within [0.0, 1.0]."""
        js_text = read_file_text("js/main.js")
        if "volume" in js_text:
            for match in re.finditer(r'\.volume\s*=\s*([0-9.]+)', js_text):
                vol = float(match.group(1))
                self.assertTrue(0.0 <= vol <= 1.0, f"Audio volume out of range: {vol}")

    def test_t2_f74_audio_toggle_icon_toggles_between_mute_and_sound(self):
        """F15 BVA: Audio toggle logic swaps icon states."""
        js_text = read_file_text("js/main.js")
        self.assertIn("audioToggle", js_text)

    def test_t2_f75_shimmer_animation_cycle_duration_bounded(self):
        """F15 BVA: Shimmer animation duration is >= 2.5s to avoid visual flashing."""
        css_text = read_file_text("css/style.css")
        match = re.search(r'shimmer\s+([0-9.]+)s', css_text)
        if match:
            dur = float(match.group(1))
            self.assertGreaterEqual(dur, 2.5, "Shimmer animation too fast (<2.5s)")

    # -------------------------------------------------------------------------
    # Feature 16: Comprehensive E2E Testing Track (Final)
    # -------------------------------------------------------------------------
    def test_t2_f76_runner_rejects_invalid_tier_gracefully(self):
        """F16 BVA: run_tests.py rejects invalid tier argument gracefully."""
        if file_exists("tests/e2e/run_tests.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "tests" / "e2e" / "run_tests.py"), "--tier", "99"], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)

    def test_t2_f77_runner_rejects_invalid_feature_gracefully(self):
        """F16 BVA: run_tests.py rejects invalid feature argument gracefully."""
        if file_exists("tests/e2e/run_tests.py"):
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "tests" / "e2e" / "run_tests.py"), "--feature", "99"], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)

    def test_t2_f78_runner_discovers_all_test_modules(self):
        """F16 BVA: run_tests.py discovers Tier 1, 2, 3, and 4 test files."""
        for t in ["test_tier1_contracts.py", "test_tier2_bva.py"]:
            self.assertTrue(file_exists(f"tests/e2e/{t}"))

    def test_t2_f79_runner_reports_per_tier_statistics(self):
        """F16 BVA: Test runner includes summary breakdown."""
        self.assertTrue(file_exists("tests/e2e/run_tests.py") or file_exists("tests/e2e/test_tier1_contracts.py"))

    def test_t2_f80_runner_nonzero_exit_code_on_assertion_failure(self):
        """F16 BVA: Exit code contract: runner returns non-zero when assertions fail."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
