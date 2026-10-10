#!/usr/bin/env python3
"""
Master E2E Test Runner for Khujand Museum Website Modernization.
Zero non-standard dependencies (Pure Python 3 standard library).

Usage:
    python tests/e2e/run_tests.py                   # Run all 184 tests across Tiers 1-4
    python tests/e2e/run_tests.py --tier 1          # Run Tier 1 tests only (80 tests)
    python tests/e2e/run_tests.py --tier 2          # Run Tier 2 tests only (80 tests)
    python tests/e2e/run_tests.py --tier 3          # Run Tier 3 tests only (16 tests)
    python tests/e2e/run_tests.py --tier 4          # Run Tier 4 tests only (8 tests)
    python tests/e2e/run_tests.py --milestone M2    # Run tests covering Milestone M2
    python tests/e2e/run_tests.py --feature 5       # Run tests covering Feature 5
    python tests/e2e/run_tests.py --verbose         # Detailed output per test
    python tests/e2e/run_tests.py --json report.json # Output machine-readable JSON report
"""

import os
import sys
import time
import json
import argparse
import unittest
from pathlib import Path
from io import StringIO
from typing import Dict, List, Any, Optional

# Ensure project root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure robust stdout encoding on Windows for Cyrillic and Tajik characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


from tests.e2e.test_tier1_contracts import TestTier1Contracts
from tests.e2e.test_tier2_bva import TestTier2BVA
from tests.e2e.test_tier3_pairwise import TestTier3Pairwise
from tests.e2e.test_tier4_stress import TestTier4Stress

# Feature catalog metadata mapping
FEATURE_METADATA = {
    1: {"name": "Authentic Local Media Migration", "milestone": "M1", "tier1": 5, "tier2": 5},
    2: {"name": "Virtual Tour File Removal", "milestone": "M2", "tier1": 5, "tier2": 5},
    3: {"name": "Tour Promo Banner Elimination", "milestone": "M2", "tier1": 5, "tier2": 5},
    4: {"name": "Navigation & Footer Tour Link Removal", "milestone": "M2", "tier1": 5, "tier2": 5},
    5: {"name": "Sitemap Validation", "milestone": "M2", "tier1": 5, "tier2": 5},
    6: {"name": "3D Gold & Claymorphism Icons", "milestone": "M3", "tier1": 5, "tier2": 5},
    7: {"name": "Decoupled i18n Icon Rendering", "milestone": "M3", "tier1": 5, "tier2": 5},
    8: {"name": "4-Epoch WebGL Scroll-World", "milestone": "M4", "tier1": 5, "tier2": 5},
    9: {"name": "Cinematic Video Scroll-World Flythrough", "milestone": "M4", "tier1": 5, "tier2": 5},
    10: {"name": "60 FPS WebGL Performance Optimization", "milestone": "M4", "tier1": 5, "tier2": 5},
    11: {"name": "GAN-Style Auto-Improve Engine", "milestone": "M5", "tier1": 5, "tier2": 5},
    12: {"name": "Museum Rubric Text Optimization", "milestone": "M5", "tier1": 5, "tier2": 5},
    13: {"name": "3D Tilt Cards with Specular Glare", "milestone": "M6", "tier1": 5, "tier2": 5},
    14: {"name": "Cinematic Staggered Reveals", "milestone": "M6", "tier1": 5, "tier2": 5},
    15: {"name": "Micro-Interactions & Parallax", "milestone": "M6", "tier1": 5, "tier2": 5},
    16: {"name": "Comprehensive E2E Testing Track", "milestone": "Final", "tier1": 5, "tier2": 5},
}

FEATURE_TO_TESTS_MAP = {
    1: ["f01", "f02", "f03", "f04", "f05"],
    2: ["f06", "f07", "f08", "f09", "f10"],
    3: ["f11", "f12", "f13", "f14", "f15"],
    4: ["f16", "f17", "f18", "f19", "f20"],
    5: ["f21", "f22", "f23", "f24", "f25"],
    6: ["f26", "f27", "f28", "f29", "f30"],
    7: ["f31", "f32", "f33", "f34", "f35"],
    8: ["f36", "f37", "f38", "f39", "f40"],
    9: ["f41", "f42", "f43", "f44", "f45"],
    10: ["f46", "f47", "f48", "f49", "f50"],
    11: ["f51", "f52", "f53", "f54", "f55"],
    12: ["f56", "f57", "f58", "f59", "f60"],
    13: ["f61", "f62", "f63", "f64", "f65"],
    14: ["f66", "f67", "f68", "f69", "f70"],
    15: ["f71", "f72", "f73", "f74", "f75"],
    16: ["f76", "f77", "f78", "f79", "f80"],
}


class DetailedTestResult(unittest.TestResult):
    """Custom test result tracking per-test metadata, duration, and tier."""

    def __init__(self, tier_name: str, verbose: bool = False):
        super().__init__()
        self.tier_name = tier_name
        self.verbose = verbose
        self.records: List[Dict[str, Any]] = []
        self._test_start: float = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._test_start = time.time()
        if self.verbose:
            doc = test.shortDescription() or ""
            sys.stdout.write(f"  [{self.tier_name}] {test._testMethodName} ({doc[:40]}...): ")
            sys.stdout.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.time() - self._test_start
        self.records.append({
            "test": test._testMethodName,
            "tier": self.tier_name,
            "status": "PASS",
            "doc": test.shortDescription() or "",
            "elapsed_ms": round(elapsed * 1000, 2),
            "error": None,
        })
        if self.verbose:
            sys.stdout.write("PASS\n")
            sys.stdout.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.time() - self._test_start
        err_msg = self._exc_info_to_string(err, test)
        self.records.append({
            "test": test._testMethodName,
            "tier": self.tier_name,
            "status": "FAIL",
            "doc": test.shortDescription() or "",
            "elapsed_ms": round(elapsed * 1000, 2),
            "error": err_msg.strip(),
        })
        if self.verbose:
            sys.stdout.write("FAIL\n")
            sys.stdout.flush()

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.time() - self._test_start
        err_msg = self._exc_info_to_string(err, test)
        self.records.append({
            "test": test._testMethodName,
            "tier": self.tier_name,
            "status": "ERROR",
            "doc": test.shortDescription() or "",
            "elapsed_ms": round(elapsed * 1000, 2),
            "error": err_msg.strip(),
        })
        if self.verbose:
            sys.stdout.write("ERROR\n")
            sys.stdout.flush()


def filter_test_suite(test_class, feature_num: Optional[int] = None, milestone: Optional[str] = None) -> unittest.TestSuite:
    """Filter test cases in a class by feature number or milestone."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    all_tests = loader.loadTestsFromTestCase(test_class)

    target_tokens = []
    if feature_num is not None:
        if feature_num in FEATURE_TO_TESTS_MAP:
            target_tokens.extend(FEATURE_TO_TESTS_MAP[feature_num])
    elif milestone is not None:
        ms_upper = milestone.upper()
        for f_num, meta in FEATURE_METADATA.items():
            if meta["milestone"].upper() == ms_upper:
                target_tokens.extend(FEATURE_TO_TESTS_MAP.get(f_num, []))

    for test in all_tests:
        method_name = test._testMethodName
        if target_tokens:
            if any(tok in method_name for tok in target_tokens):
                suite.addTest(test)
        else:
            suite.addTest(test)
    return suite


def run_tier(tier_num: int, tier_name: str, test_class, feature_num: Optional[int], milestone: Optional[str], verbose: bool) -> DetailedTestResult:
    """Run tests for a single tier and return DetailedTestResult."""
    suite = filter_test_suite(test_class, feature_num=feature_num, milestone=milestone)
    result = DetailedTestResult(tier_name=tier_name, verbose=verbose)
    suite.run(result)
    return result


def print_banner():
    print("=" * 80)
    print(" KHUJAND MUSEUM MODERNIZATION — STANDALONE E2E TEST RUNNER")
    print(" Framework: Pure Python 3 (zero non-standard dependencies)")
    print("=" * 80)


def print_tier_summary(tier_name: str, result: DetailedTestResult, min_threshold: int):
    passed = len([r for r in result.records if r["status"] == "PASS"])
    failed = len([r for r in result.records if r["status"] == "FAIL"])
    errors = len([r for r in result.records if r["status"] == "ERROR"])
    total = len(result.records)

    badge = "[OK]" if (failed == 0 and errors == 0 and total >= min_threshold) else "[ATTENTION]"
    print(f"\n{badge} {tier_name}: {passed}/{total} Passed (Failed: {failed}, Errors: {errors}) | Threshold: >={min_threshold}")

    if failed > 0 or errors > 0:
        print("  " + "-" * 76)
        print("  Diagnostics for Failures/Errors:")
        for r in result.records:
            if r["status"] in ("FAIL", "ERROR"):
                first_err_line = r["error"].splitlines()[-1] if r["error"] else "Unknown error"
                print(f"  * {r['test']}: {first_err_line}")


def print_feature_matrix(all_records: List[Dict[str, Any]]):
    print("\n" + "=" * 80)
    print(" FEATURE INVENTORY COVERAGE MATRIX (16 FEATURES)")
    print("=" * 80)
    print(f" {'#':<3} | {'Feature Name':<38} | {'MS':<5} | {'Tier 1':<8} | {'Tier 2':<8} | {'Status':<10}")
    print("-" * 80)

    for f_num, meta in FEATURE_METADATA.items():
        tokens = FEATURE_TO_TESTS_MAP.get(f_num, [])
        # Find matching records
        t1_records = [r for r in all_records if r["tier"] == "Tier 1" and any(t in r["test"] for t in tokens)]
        t2_records = [r for r in all_records if r["tier"] == "Tier 2" and any(t in r["test"] for t in tokens)]

        t1_pass = len([r for r in t1_records if r["status"] == "PASS"])
        t1_total = len(t1_records)
        t2_pass = len([r for r in t2_records if r["status"] == "PASS"])
        t2_total = len(t2_records)

        status = "PASS" if (t1_pass == t1_total and t2_pass == t2_total and (t1_total + t2_total) > 0) else "FAIL"
        t1_str = f"{t1_pass}/{t1_total}" if t1_total > 0 else "-"
        t2_str = f"{t2_pass}/{t2_total}" if t2_total > 0 else "-"

        print(f" {f_num:<3} | {meta['name'][:38]:<38} | {meta['milestone']:<5} | {t1_str:<8} | {t2_str:<8} | {status:<10}")
    print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Standalone E2E Test Runner for Khujand Museum Modernization")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run a specific test tier (1, 2, 3, or 4)")
    parser.add_argument("--milestone", type=str, choices=["M1", "M2", "M3", "M4", "M5", "M6", "Final", "m1", "m2", "m3", "m4", "m5", "m6", "final"], help="Filter tests by milestone (e.g. M2)")
    parser.add_argument("--feature", type=int, choices=list(range(1, 17)), help="Filter tests by feature number (1-16)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose per-test diagnostics")
    parser.add_argument("--json", type=str, help="Save machine-readable JSON results to specified file path")

    args = parser.parse_args()

    print_banner()

    tiers_to_run = []
    if args.tier is None:
        tiers_to_run = [
            (1, "Tier 1: Functional & Contracts", TestTier1Contracts, 80),
            (2, "Tier 2: Boundary Value Analysis", TestTier2BVA, 80),
            (3, "Tier 3: Pairwise & Integration", TestTier3Pairwise, 16),
            (4, "Tier 4: Workload & Stress", TestTier4Stress, 8),
        ]
    elif args.tier == 1:
        tiers_to_run = [(1, "Tier 1: Functional & Contracts", TestTier1Contracts, 80)]
    elif args.tier == 2:
        tiers_to_run = [(2, "Tier 2: Boundary Value Analysis", TestTier2BVA, 80)]
    elif args.tier == 3:
        tiers_to_run = [(3, "Tier 3: Pairwise & Integration", TestTier3Pairwise, 16)]
    elif args.tier == 4:
        tiers_to_run = [(4, "Tier 4: Workload & Stress", TestTier4Stress, 8)]

    all_results: List[DetailedTestResult] = []
    all_records: List[Dict[str, Any]] = []

    start_total_time = time.time()

    for t_num, t_name, t_cls, t_thresh in tiers_to_run:
        if args.verbose:
            print(f"\n>>> Running {t_name}...")
        res = run_tier(t_num, t_name.split(':')[0], t_cls, args.feature, args.milestone, args.verbose)
        all_results.append(res)
        all_records.extend(res.records)
        print_tier_summary(t_name, res, t_thresh if (args.milestone is None and args.feature is None) else 0)

    total_duration = time.time() - start_total_time

    total_executed = len(all_records)
    total_passed = len([r for r in all_records if r["status"] == "PASS"])
    total_failed = len([r for r in all_records if r["status"] == "FAIL"])
    total_errors = len([r for r in all_records if r["status"] == "ERROR"])

    # If full run, display feature matrix
    if args.tier is None and args.milestone is None and args.feature is None:
        print_feature_matrix(all_records)

    print("\n" + "=" * 80)
    print(f" TEST RUN EXECUTION SUMMARY")
    print(f" Total Tests Executed : {total_executed}")
    print(f" Passed               : {total_passed}")
    print(f" Failed               : {total_failed}")
    print(f" Errors               : {total_errors}")
    print(f" Total Duration       : {total_duration:.2f} seconds")
    print("=" * 80)

    if args.json:
        out_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total": total_executed,
            "passed": total_passed,
            "failed": total_failed,
            "errors": total_errors,
            "duration_seconds": round(total_duration, 2),
            "records": all_records,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out_payload, f, indent=2, ensure_ascii=False)
        print(f"JSON report written to: {args.json}")

    # Exit code: 0 if all tests passed and total > 0, 1 on failure
    if total_failed > 0 or total_errors > 0 or total_executed == 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
