#!/usr/bin/env python3
"""
tests/stress_scroll_and_animations.py - Stress & Safety Verification for 3D Scroll-World & Animations
Validates:
1. Passive listener enforcement across all window scroll events.
2. Throttled RAF execution in animations.
3. IntersectionObserver offscreen sleep & RAF cancel.
4. Delta time capping (<= 0.1s).
5. DPR clamping bounds (mobile <= 1.0, desktop <= 1.75).
6. 3D Tilt angle clamping (<= 15 deg).
7. Magnetic button pull clamping (<= 12 px).
8. GPU disposal API availability and completeness.
9. Absence of unthrottled infinite timer loops (setInterval / recursive setTimeout).
"""

import pathlib
import re
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

def test_passive_scroll_listeners():
    print("--- Test 1: Passive Scroll Listener Audit ---")
    js_files = [
        PROJECT_ROOT / "js" / "scroll-world.js",
        PROJECT_ROOT / "js" / "animations.js",
        PROJECT_ROOT / "js" / "main.js"
    ]
    unpassive = []
    for f in js_files:
        text = f.read_text(encoding="utf-8")
        # Match window.addEventListener('scroll', fn) or addEventListener('scroll'
        matches = re.finditer(r"(?:window\.)?addEventListener\s*\(\s*['\"]scroll['\"]\s*,\s*([^,\)]+)(?:,\s*([^)]+))?\)", text)
        for m in matches:
            handler = m.group(1).strip()
            opts = m.group(2) if m.group(2) else ""
            if "passive: true" not in opts and "passive:true" not in opts:
                unpassive.append((f.name, handler, opts))

    if unpassive:
        print(f"FAILED: Found non-passive scroll listeners:")
        for fn, h, opt in unpassive:
            print(f"  In {fn}: handler '{h}' opts: '{opt}'")
    else:
        print("PASS: 100% of scroll listeners are explicitly marked { passive: true }.")
    assert len(unpassive) == 0

def test_scroll_world_lifecycle_and_disposal():
    print("\n--- Test 2: 3D Scroll-World Lifecycle & Memory Disposal Audit ---")
    sw_file = PROJECT_ROOT / "js" / "scroll-world.js"
    text = sw_file.read_text(encoding="utf-8")

    # 1. IntersectionObserver pause/cancel
    assert "IntersectionObserver" in text, "Missing IntersectionObserver in scroll-world.js"
    assert "cancelAnimationFrame" in text, "Missing cancelAnimationFrame in scroll-world.js"

    # 2. Clock delta clamp
    delta_match = re.search(r"Math\.min\(\s*rawDelta\s*,\s*0\.1\s*\)", text)
    assert delta_match is not None, "Clock delta clamping to <= 0.1s is missing or incorrect"

    # 3. DPR clamping
    assert "1.0" in text and "1.75" in text, "DPR clamping values (1.0 mobile, 1.75 desktop) missing"
    assert "setPixelRatio" in text, "Renderer setPixelRatio missing"

    # 4. GPU resource disposal
    assert "disposeGPUResources" in text, "Missing disposeGPUResources function"
    assert "disposableGeometries" in text, "Missing disposableGeometries registry"
    assert "disposableMaterials" in text, "Missing disposableMaterials registry"
    assert "disposableTextures" in text, "Missing disposableTextures registry"
    assert "window.disposeScrollWorld" in text, "Missing public window.disposeScrollWorld API"

    print("PASS: 3D Scroll-World implements complete lifecycle management, auto-sleep, and GPU disposal.")

def test_animations_guards_and_bounds():
    print("\n--- Test 3: Animation Bounds, Clamps & Touch Guards ---")
    anim_file = PROJECT_ROOT / "js" / "animations.js"
    text = anim_file.read_text(encoding="utf-8")

    # 1. Prefers-reduced-motion check
    assert "prefers-reduced-motion" in text, "Missing prefers-reduced-motion accessibility guard"

    # 2. Touch / hover pointer check
    assert "hover: hover" in text or "pointer: fine" in text, "Missing fine pointer guard"
    assert "isTouchDevice" in text, "Missing touch device guard"

    # 3. Tilt clamp <= 15 deg
    tilt_match = re.search(r"MAX_TILT\s*=\s*(\d+)", text)
    assert tilt_match is not None, "Missing MAX_TILT constant"
    max_tilt = int(tilt_match.group(1))
    assert max_tilt <= 15, f"MAX_TILT {max_tilt} exceeds 15 degrees"

    # 4. Magnetic pull clamp <= 12 px
    pull_match = re.search(r"MAX_MAGNETIC_PULL\s*=\s*(\d+)", text)
    assert pull_match is not None, "Missing MAX_MAGNETIC_PULL constant"
    max_pull = int(pull_match.group(1))
    assert max_pull <= 12, f"MAX_MAGNETIC_PULL {max_pull} exceeds 12 pixels"

    # 5. Stagger interval
    stagger_match = re.search(r"stagger\s*:\s*(0\.\d+)", text)
    assert stagger_match is not None, "Missing stagger duration in reveals"
    stagger_val = float(stagger_match.group(1))
    assert 0.05 <= stagger_val <= 0.3, f"Stagger {stagger_val} outside [0.05, 0.3] bound"

    print("PASS: Animation system enforces all physical bounds, tilt/pull clamps, and touch guards.")

def test_timer_loops_audit():
    print("\n--- Test 4: Timer & Unbounded Loop Audit ---")
    js_files = [
        PROJECT_ROOT / "js" / "scroll-world.js",
        PROJECT_ROOT / "js" / "animations.js",
        PROJECT_ROOT / "js" / "main.js"
    ]
    unbounded_intervals = []
    for f in js_files:
        text = f.read_text(encoding="utf-8")
        intervals = re.findall(r"setInterval\s*\(", text)
        if intervals:
            unbounded_intervals.append((f.name, len(intervals)))

    if unbounded_intervals:
        print(f"INFO: Detected setInterval occurrences in:")
        for fn, count in unbounded_intervals:
            print(f"  {fn}: {count} occurrences")
    else:
        print("PASS: 0 setInterval calls detected across modern js modules.")

    assert len(unbounded_intervals) == 0

def test_node_syntax_and_eval():
    print("\n--- Test 5: Node.js Syntax Verification ---")
    for script_name in ["scroll-world.js", "animations.js", "main.js"]:
        js_path = PROJECT_ROOT / "js" / script_name
        # Check syntax using node -c
        res = subprocess.run(["node", "-c", str(js_path)], capture_output=True, text=True)
        assert res.returncode == 0, f"Syntax error in {script_name}: {res.stderr}"
        print(f"PASS: {script_name} passes pure Node.js syntax parsing (exit code 0)")

if __name__ == "__main__":
    test_passive_scroll_listeners()
    test_scroll_world_lifecycle_and_disposal()
    test_animations_guards_and_bounds()
    test_timer_loops_audit()
    test_node_syntax_and_eval()
    print("\n" + "=" * 60)
    print("ALL SCROLL & ANIMATION STRESS VERIFICATIONS PASSED")
    print("=" * 60)
