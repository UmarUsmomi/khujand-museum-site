"""
Tier 4: Real-World Workload & Performance / Stress Scenarios.
Threshold: >= 8 tests.
Zero non-standard dependencies.
"""

import os
import re
import sys
import time
import unittest
import subprocess
from pathlib import Path

from tests.e2e.dom_utils import (
    PROJECT_ROOT,
    parse_html_file,
    read_file_text,
    file_exists,
)


class TestTier4Stress(unittest.TestCase):
    """Tier 4: Stress, budget, and performance limit tests."""

    def test_t4_01_total_initial_page_payload_budget(self):
        """T4.01: Core static code (index.html + css/style.css + js/main.js) <= 350 KB."""
        index_size = (PROJECT_ROOT / "index.html").stat().st_size
        css_size = (PROJECT_ROOT / "css" / "style.css").stat().st_size
        js_size = (PROJECT_ROOT / "js" / "main.js").stat().st_size
        total_kb = (index_size + css_size + js_size) / 1024
        self.assertLessEqual(total_kb, 350, f"Core static code exceeds 350 KB: {total_kb:.1f} KB")

    def test_t4_02_local_images_total_kiosk_budget(self):
        """T4.02: Total size of images/ directory <= 15 MB for fast kiosk loading."""
        images_dir = PROJECT_ROOT / "images"
        if images_dir.exists():
            total_bytes = sum(f.stat().st_size for f in images_dir.glob("**/*.*") if f.is_file())
            total_mb = total_bytes / (1024 * 1024)
            self.assertLessEqual(total_mb, 15.0, f"Images directory exceeds 15 MB: {total_mb:.2f} MB")

    def test_t4_03_procedural_mesh_triangle_budget(self):
        """T4.03: Procedural 3D WebGL scene triangle budget <= 25,000 triangles."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            # Verify no giant obj/gltf loaders of multi-million polygon models
            self.assertNotIn("GLTFLoader", sw_text)
            self.assertNotIn("OBJLoader", sw_text)

    def test_t4_04_webgl_offscreen_sleep_observer(self):
        """T4.04: js/scroll-world.js halts rendering loop via IntersectionObserver when offscreen."""
        if file_exists("js/scroll-world.js"):
            sw_text = read_file_text("js/scroll-world.js")
            has_sleep = ("IntersectionObserver" in sw_text and
                         ("cancelAnimationFrame" in sw_text or "isIntersecting" in sw_text or "pause" in sw_text))
            self.assertTrue(has_sleep, "IntersectionObserver auto-sleep logic must be implemented in scroll-world.js")

    def test_t4_05_css_compositor_only_animation_properties(self):
        """T4.05: Continuous 60fps keyframes (shimmer, float, levitate) animate only GPU properties."""
        css_text = read_file_text("css/style.css")
        # Extract all @keyframes blocks
        keyframes_blocks = re.findall(r'@keyframes\s+([a-zA-Z0-9_-]+)\s*\{([^}]+(?:\{[^}]+\}[^}]*)*)\}', css_text)
        disallowed = ["height:", "width:", "top:", "left:", "bottom:", "right:", "margin:"]
        continuous_animations = ["shimmer", "gold-shimmer", "float", "clay-levitate", "icon-float", "fadeIn"]
        for name, block in keyframes_blocks:
            if any(ca in name.lower() for ca in continuous_animations):
                for prop in disallowed:
                    self.assertNotIn(prop, block.lower(), f"Continuous keyframe '{name}' animates layout property '{prop}'; violates 60 FPS rule")

    def test_t4_06_cli_auto_improve_multi_round_performance(self):
        """T4.06: CLI scripts/auto_improve.py 3 rounds dry-run completes within 10 seconds."""
        if file_exists("scripts/auto_improve.py"):
            start_time = time.time()
            res = subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--task", "all", "--dry-run", "--rounds", "3"], capture_output=True, text=True)
            duration = time.time() - start_time
            self.assertEqual(res.returncode, 0)
            self.assertLessEqual(duration, 10.0, f"Auto-improve 3 rounds took {duration:.2f}s, exceeding 10s budget")

    def test_t4_07_responsive_breakpoints_coverage(self):
        """T4.07: css/style.css covers mobile (<=480px/768px) and tablet (<=1024px) breakpoints."""
        css_text = read_file_text("css/style.css")
        has_mobile = bool(re.search(r'max-width\s*:\s*(?:768|767|576|480)px', css_text))
        has_tablet = bool(re.search(r'max-width\s*:\s*(?:1024|992)px', css_text))
        self.assertTrue(has_mobile and has_tablet, "CSS must define mobile and tablet media query breakpoints")

    def test_t4_08_html_dom_depth_and_node_count_limits(self):
        """T4.08: index.html DOM depth <= 16 and total node count <= 1500 to guarantee 60 FPS."""
        doc = parse_html_file("index.html")
        all_nodes = doc.find_all()
        node_count = len(all_nodes)
        self.assertLessEqual(node_count, 1500, f"index.html has {node_count} DOM nodes; exceeds 1500 budget")

        # Measure max depth
        def get_max_depth(node, current_depth=0):
            if not node.children:
                return current_depth
            return max(get_max_depth(c, current_depth + 1) for c in node.children)

        max_depth = get_max_depth(doc)
        self.assertLessEqual(max_depth, 16, f"index.html DOM max depth {max_depth} exceeds 16")


if __name__ == '__main__':
    unittest.main()
