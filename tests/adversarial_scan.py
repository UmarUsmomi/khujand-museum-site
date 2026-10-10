#!/usr/bin/env python3
"""
tests/adversarial_scan.py - Repository Anomaly & Asset Integrity Scanner
Checks:
1. Leftover Unsplash links in production code (HTML, CSS, JS).
2. Flat emojis in production HTML.
3. Video files (*.mp4, *.webm, etc.) and <video> tags.
4. Broken image links (HTML img src, CSS url).
5. References to deleted virtual-tour.html.
6. Sitemap.xml validity.
"""

import os
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

PROD_HTML_FILES = [PROJECT_ROOT / "index.html"] + list((PROJECT_ROOT / "pages").glob("*.html"))
PROD_CSS_FILES = list((PROJECT_ROOT / "css").glob("*.css"))
PROD_JS_FILES = [f for f in (PROJECT_ROOT / "js").glob("*.js") if "vendor" not in str(f)]

ALL_PROD_FILES = PROD_HTML_FILES + PROD_CSS_FILES + PROD_JS_FILES

# Emoji regex covering common emojis including those listed in R4
EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]"
)

# Target emojis specifically listed in Requirement R4:
# 🏛️, 🏺, 🎧, 🏰, 🎫, 📍, 📞, 📧, ⭐, 🔊
TARGET_R4_EMOJIS = ["🏛", "🏺", "🎧", "🏰", "🎫", "📍", "📞", "📧", "⭐", "🔊"]

def check_unsplash_links():
    print("--- Check 1: Unsplash Links in Production Files ---")
    violations = []
    pattern = re.compile(r"unsplash\.com", re.IGNORECASE)
    for p in ALL_PROD_FILES:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        matches = [m.start() for m in pattern.finditer(text)]
        if matches:
            violations.append((p.relative_to(PROJECT_ROOT), len(matches)))
    
    if violations:
        print(f"FAILED: Found Unsplash references in {len(violations)} files:")
        for path, count in violations:
            print(f"  {path}: {count} occurrences")
    else:
        print("PASS: 0 Unsplash links found in production HTML, CSS, JS files.")
    return len(violations) == 0

def check_video_presence():
    print("\n--- Check 2: Video Files and Video Elements ---")
    video_path = PROJECT_ROOT / "videos" / "flythrough-epochs.mp4"
    if not video_path.exists():
        print(f"FAILED: Expected flythrough video at {video_path} not found.")
        return False

    # Check <video> tag in index.html
    index_text = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
    has_video_tag = bool(re.search(r"<\s*video\b[^>]*scroll-world-video", index_text, re.IGNORECASE))
    if not has_video_tag:
        print("FAILED: index.html missing #scroll-world-video element.")
        return False

    print("PASS: Authentic flythrough video present and embedded into Scroll-World.")
    return True

def check_flat_emojis():
    print("\n--- Check 3: Flat Emojis in Production HTML ---")
    r4_violations = []
    any_emoji_violations = []

    for p in PROD_HTML_FILES:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            # Check target R4 emojis
            for em in TARGET_R4_EMOJIS:
                if em in line:
                    r4_violations.append((p.relative_to(PROJECT_ROOT), idx, em, line.strip()[:80]))
            
            # Check general emojis
            emojis_found = EMOJI_PATTERN.findall(line)
            if emojis_found:
                any_emoji_violations.append((p.relative_to(PROJECT_ROOT), idx, "".join(emojis_found), line.strip()[:80]))

    if r4_violations:
        print(f"FAILED: Found {len(r4_violations)} R4 target emojis in production HTML:")
        for path, line_no, em, snippet in r4_violations[:10]:
            print(f"  {path}:{line_no} [{em}] {snippet}")
    else:
        print("PASS: 0 Requirement R4 target emojis (🏛️, 🏺, 🎧, 🏰, 🎫, 📍, 📞, 📧, ⭐, 🔊) found in production HTML.")

    print(f"INFO: Total Unicode symbols detected across HTML: {len(any_emoji_violations)}")
    return len(r4_violations) == 0

def check_broken_image_links():
    print("\n--- Check 4: Broken Image References in HTML & CSS ---")
    broken = []
    total_checked = 0

    # 1. HTML <img src="..."> and srcset
    img_src_regex = re.compile(r"""(?:src|data-src)=["']([^"']+)["']""", re.IGNORECASE)
    for p in PROD_HTML_FILES:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for match in img_src_regex.finditer(text):
            src = match.group(1).strip()
            if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
                continue
            # Strip query params / hash
            clean_src = src.split("?")[0].split("#")[0]
            if not clean_src:
                continue
            
            total_checked += 1
            # Resolve relative to HTML file location
            target_file = (p.parent / clean_src).resolve()
            if not target_file.exists():
                broken.append((p.relative_to(PROJECT_ROOT), src, str(target_file)))

    # 2. CSS url(...)
    css_url_regex = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", re.IGNORECASE)
    for p in PROD_CSS_FILES:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for match in css_url_regex.finditer(text):
            src = match.group(1).strip()
            if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
                continue
            clean_src = src.split("?")[0].split("#")[0]
            if not clean_src:
                continue
            total_checked += 1
            target_file = (p.parent / clean_src).resolve()
            if not target_file.exists():
                broken.append((p.relative_to(PROJECT_ROOT), src, str(target_file)))

    print(f"Total local image/asset references checked: {total_checked}")
    if broken:
        print(f"FAILED: Found {len(broken)} broken asset links:")
        for origin, ref, resolved in broken:
            print(f"  In {origin}: '{ref}' -> file does not exist at {resolved}")
    else:
        print(f"PASS: All {total_checked} referenced local assets exist on disk.")

    return len(broken) == 0

def check_virtual_tour_references():
    print("\n--- Check 5: References to Removed virtual-tour.html ---")
    vt_file = PROJECT_ROOT / "pages" / "virtual-tour.html"
    if vt_file.exists():
        print(f"FAILED: pages/virtual-tour.html still exists on disk!")
        return False
    else:
        print("PASS: pages/virtual-tour.html is confirmed deleted.")

    vt_refs = []
    pattern = re.compile(r"virtual-tour\.html", re.IGNORECASE)
    for p in ALL_PROD_FILES:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(text):
            vt_refs.append(p.relative_to(PROJECT_ROOT))

    if vt_refs:
        print(f"FAILED: Found references to virtual-tour.html in {len(vt_refs)} files:")
        for r in vt_refs:
            print(f"  {r}")
    else:
        print("PASS: 0 references to virtual-tour.html in production files.")

    return not vt_file.exists() and len(vt_refs) == 0

def check_sitemap():
    print("\n--- Check 6: Sitemap.xml Integrity ---")
    sitemap_file = PROJECT_ROOT / "sitemap.xml"
    if not sitemap_file.exists():
        print("FAILED: sitemap.xml does not exist")
        return False

    try:
        tree = ET.parse(sitemap_file)
        root = tree.getroot()
        urls = []
        for elem in root.iter():
            if elem.tag.endswith("loc"):
                urls.append(elem.text.strip() if elem.text else "")
        
        print(f"Sitemap parsed successfully. Total URLs: {len(urls)}")
        for u in urls:
            print(f"  - {u}")
            if "virtual-tour" in u.lower():
                print(f"FAILED: virtual-tour found in sitemap URL: {u}")
                return False
        print("PASS: sitemap.xml is valid XML and contains no virtual-tour references.")
        return True
    except Exception as e:
        print(f"FAILED: parsing sitemap.xml error: {e}")
        return False

if __name__ == "__main__":
    c1 = check_unsplash_links()
    c2 = check_video_presence()
    c3 = check_flat_emojis()
    c4 = check_broken_image_links()
    c5 = check_virtual_tour_references()
    c6 = check_sitemap()

    all_passed = c1 and c2 and c3 and c4 and c5 and c6
    print("\n" + "=" * 60)
    print(f"OVERALL SCAN RESULT: {'ALL PASS' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)
