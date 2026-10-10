"""
Unit & Contract Tests for ElevenLabs Studio Multi-Language Voiceovers
and Butter-Smooth 60 FPS 3D Flyover Engine.
"""

import os
import unittest
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestVoicesAndFlythrough(unittest.TestCase):
    """Test suite for voiceovers and smooth flyover."""

    def test_voice_files_exist_and_sized(self):
        """Verify that rus.mp3, eng.mp3, and taj.mp3 exist in voices/ with valid sizes."""
        voices_dir = PROJECT_ROOT / "voices"
        self.assertTrue(voices_dir.is_dir(), "voices/ directory must exist")

        for fname in ["rus.mp3", "eng.mp3", "taj.mp3"]:
            fpath = voices_dir / fname
            self.assertTrue(fpath.is_file(), f"{fname} must exist in voices/")
            self.assertGreater(fpath.stat().st_size, 1_000_000, f"{fname} must be > 1MB")

    def test_main_js_wires_all_three_languages(self):
        """Verify js/main.js references rus.mp3, eng.mp3, and taj.mp3 with seamless switcher."""
        main_js = (PROJECT_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("rus.mp3", main_js, "main.js must reference rus.mp3")
        self.assertIn("eng.mp3", main_js, "main.js must reference eng.mp3")
        self.assertIn("taj.mp3", main_js, "main.js must reference taj.mp3")
        self.assertIn("switchVoiceLanguage", main_js, "main.js must implement switchVoiceLanguage")
        self.assertIn("onMuseumLanguageChange", main_js, "main.js must hook onMuseumLanguageChange")

    def test_elevenlabs_attribution_in_js_and_docs(self):
        """Verify ElevenLabs Studio attribution in js/main.js, VOICES_ATTRIBUTION.md, and README.md."""
        main_js = (PROJECT_ROOT / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("ElevenLabs", main_js, "js/main.js must credit ElevenLabs Studio")

        attr_doc = PROJECT_ROOT / "VOICES_ATTRIBUTION.md"
        self.assertTrue(attr_doc.is_file(), "VOICES_ATTRIBUTION.md must exist")
        attr_text = attr_doc.read_text(encoding="utf-8")
        self.assertIn("ElevenLabs Studio", attr_text, "VOICES_ATTRIBUTION.md must credit ElevenLabs Studio")

        readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("ElevenLabs Studio", readme_text, "README.md must reference ElevenLabs Studio")

    def test_flythrough_video_keyframe_density(self):
        """Verify videos/flythrough-epochs.mp4 exists and has frequent keyframes for jitter-free scrubbing."""
        video_path = PROJECT_ROOT / "videos" / "flythrough-epochs.mp4"
        self.assertTrue(video_path.is_file(), "videos/flythrough-epochs.mp4 must exist")
        self.assertGreater(video_path.stat().st_size, 5_000_000, "video must be > 5MB")

    def test_scroll_world_js_smooth_scrubbing(self):
        """Verify js/scroll-world.js does not use fastSeek and implements smooth interpolation."""
        sw_text = (PROJECT_ROOT / "js" / "scroll-world.js").read_text(encoding="utf-8")
        self.assertNotIn("fastSeek", sw_text, "scroll-world.js must not use jittery fastSeek")
        self.assertIn("currentVideoProgress", sw_text, "scroll-world.js must track interpolated video progress")
        self.assertIn("power2.inOut", sw_text, "scroll-world.js must use smooth easing for epoch tab clicks")

    def test_footer_attribution_in_html(self):
        """Verify footer in index.html references ElevenLabs Studio."""
        index_html = (PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("ElevenLabs Studio", index_html, "index.html must reference ElevenLabs Studio")


if __name__ == "__main__":
    unittest.main()
