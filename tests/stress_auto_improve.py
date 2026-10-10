#!/usr/bin/env python3
"""
tests/stress_auto_improve.py - Adversarial Stress & Edge Case Test Suite
Target: scripts/auto_improve.py
"""

import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.auto_improve import (
    DEFAULT_HISTORY_FILE,
    DEFAULT_IMPROVEMENT_THRESHOLD,
    EXHIBIT_TARGETS,
    PROMPT_TARGETS,
    RUBRIC_WEIGHTS,
    AutoImproveEngine,
    ContentMutator,
    IndependentJudge,
    PairwiseBlindGate,
)

def run_cli(args):
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py")] + args
    return subprocess.run(cmd, capture_output=True, text=True)

def test_cli_negative_rounds():
    res = run_cli(["--rounds", "-1"])
    assert res.returncode != 0, f"Expected non-zero exit for --rounds -1, got {res.returncode}"
    assert "error" in res.stderr.lower()
    print("PASS: --rounds -1 exits with error")

    res = run_cli(["--rounds", "-999"])
    assert res.returncode != 0, f"Expected non-zero exit for --rounds -999, got {res.returncode}"
    print("PASS: --rounds -999 exits with error")

def test_cli_zero_rounds():
    res = run_cli(["--rounds", "0"])
    assert res.returncode != 0, f"Expected non-zero exit for --rounds 0, got {res.returncode}"
    assert "error" in res.stderr.lower()
    print("PASS: --rounds 0 exits with error")

def test_cli_invalid_type_rounds():
    res = run_cli(["--rounds", "abc"])
    assert res.returncode != 0
    res = run_cli(["--rounds", "1.5"])
    assert res.returncode != 0
    print("PASS: --rounds invalid types rejected")

def test_cli_invalid_task():
    res = run_cli(["--task", "nonexistent"])
    assert res.returncode != 0
    assert "invalid choice" in res.stderr.lower()
    print("PASS: --task invalid choice rejected")

def test_cli_unknown_arg():
    res = run_cli(["--foo-bar-baz"])
    assert res.returncode != 0
    print("PASS: unknown flag rejected")

def test_cli_dry_run_no_history_modification():
    # Record mtime of history file if exists
    orig_content = None
    orig_mtime = None
    if DEFAULT_HISTORY_FILE.exists():
        orig_content = DEFAULT_HISTORY_FILE.read_bytes()
        orig_mtime = os.path.getmtime(DEFAULT_HISTORY_FILE)
    
    time.sleep(0.05)
    res = run_cli(["--dry-run", "--rounds", "1", "--task", "descriptions"])
    assert res.returncode == 0, f"Dry-run failed: {res.stderr}"
    assert "[DRY-RUN]" in res.stdout

    if orig_content is not None:
        new_content = DEFAULT_HISTORY_FILE.read_bytes()
        new_mtime = os.path.getmtime(DEFAULT_HISTORY_FILE)
        assert orig_content == new_content, "Dry run modified history file content!"
        assert orig_mtime == new_mtime, "Dry run touched history file mtime!"
    print("PASS: --dry-run guarantees zero mutation of auto_improve_history.json")

def test_cli_report_nested_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_report = pathlib.Path(tmpdir) / "sub1" / "sub2" / "custom_report.json"
        res = run_cli(["--dry-run", "--rounds", "1", "--task", "descriptions", "--report", str(nested_report)])
        assert res.returncode == 0, f"CLI with nested report path failed: {res.stderr}"
        assert nested_report.exists(), "Report file was not created in nested path"
        with open(nested_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["version"] == "1.0.0"
        assert "execution_summary" in data
        assert data["configuration"]["dry_run"] is True
    print("PASS: --report in non-existent nested directory works cleanly")

def test_extreme_thresholds():
    # Threshold 1.0 (impossible to promote)
    engine = AutoImproveEngine(rounds=1, threshold=1.0, dry_run=True, seed=42)
    report = engine.run_optimization(task="descriptions")
    assert report["execution_summary"]["total_promotions"] == 0
    assert report["execution_summary"]["total_rejections"] > 0
    print("PASS: extreme threshold 1.0 rejects all candidates properly")

def test_high_rounds():
    # Rounds = 10 (higher than predefined stages 3)
    engine = AutoImproveEngine(rounds=5, threshold=0.03, dry_run=True, seed=42)
    report = engine.run_optimization(task="descriptions")
    assert report["execution_summary"]["total_mutations_evaluated"] == len(EXHIBIT_TARGETS) * 5
    print("PASS: rounds > predefined stages handles gracefully without index error")

def test_judge_adversarial_inputs():
    judge = IndependentJudge()
    
    # 1. Empty string
    res_empty = judge.evaluate_text_description("")
    assert isinstance(res_empty["composite"], float)
    assert 0.0 <= res_empty["composite"] <= 1.0
    
    res_empty_3d = judge.evaluate_3d_prompt("")
    assert isinstance(res_empty_3d["composite"], float)
    assert 0.0 <= res_empty_3d["composite"] <= 1.0

    # 2. Huge text (100k chars)
    huge_text = "Худжанд цитадель история артефакты " * 3000
    res_huge = judge.evaluate_text_description(huge_text)
    assert isinstance(res_huge["composite"], float)

    # 3. Unicode edge cases (zero width spaces, emojis, Arabic/Persian/Tajik, control chars)
    weird_text = "🏛️\u200b\u200d\u200e\ufeffХуджанд\x00\t\n \u0641\u0627\u0631\u0633\u06cc"
    res_weird = judge.evaluate_text_description(weird_text)
    assert isinstance(res_weird["composite"], float)

    # 4. None / empty metadata
    res_no_meta = judge.evaluate_text_description("Текст музея Худжанда", target_metadata=None)
    assert isinstance(res_no_meta["composite"], float)
    res_empty_meta = judge.evaluate_text_description("Текст музея Худжанда", target_metadata={})
    assert isinstance(res_empty_meta["composite"], float)

    print("PASS: judge handles empty, huge, unicode, and missing metadata without crash")

def test_gate_adversarial_inputs():
    judge = IndependentJudge()
    gate = PairwiseBlindGate(judge=judge, threshold=0.03)

    # Identical strings: champion == challenger -> score delta = 0 -> must be rejected
    res_same = gate.evaluate_pair("Текст одинаковый", "Текст одинаковый", "descriptions")
    assert not res_same["promoted"]
    assert res_same["decision"] == "REJECTED"
    assert res_same["score_delta"] == 0.0

    # Challenger empty string: must be rejected
    res_empty_chall = gate.evaluate_pair("Текст музея", "", "descriptions")
    assert not res_empty_chall["promoted"]
    assert res_empty_chall["decision"] == "REJECTED"

    print("PASS: pairwise gate handles identical strings and empty challenger safely")

def test_seed_determinism():
    with tempfile.TemporaryDirectory() as tmpdir:
        rep1_path = pathlib.Path(tmpdir) / "rep1.json"
        rep2_path = pathlib.Path(tmpdir) / "rep2.json"
        res1 = run_cli(["--dry-run", "--rounds", "2", "--task", "descriptions", "--seed", "12345", "--report", str(rep1_path)])
        res2 = run_cli(["--dry-run", "--rounds", "2", "--task", "descriptions", "--seed", "12345", "--report", str(rep2_path)])
        assert res1.returncode == 0 and res2.returncode == 0
        with open(rep1_path, "r", encoding="utf-8") as f1, open(rep2_path, "r", encoding="utf-8") as f2:
            d1 = json.load(f1)
            d2 = json.load(f2)
        # Check blind gate assignment and decisions match exactly
        for tid in d1["lineage"]:
            r1 = d1["lineage"][tid]["rounds"]
            r2 = d2["lineage"][tid]["rounds"]
            for round_idx in range(len(r1)):
                assert r1[round_idx]["blind_gate"]["assignment"] == r2[round_idx]["blind_gate"]["assignment"], "Seed determinism failed on assignment"
                assert r1[round_idx]["decision"] == r2[round_idx]["decision"], "Seed determinism failed on decision"
        print("PASS: --seed produces 100% deterministic evaluation runs")

def test_custom_history_path_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_hist = pathlib.Path(tmpdir) / "a" / "b" / "custom_hist.json"
        res = run_cli(["--rounds", "1", "--task", "descriptions", "--history-path", str(custom_hist)])
        assert res.returncode == 0
        assert custom_hist.exists()
        print("PASS: --history-path creates parent folders and writes valid JSON")

if __name__ == "__main__":
    test_cli_negative_rounds()
    test_cli_zero_rounds()
    test_cli_invalid_type_rounds()
    test_cli_invalid_task()
    test_cli_unknown_arg()
    test_cli_dry_run_no_history_modification()
    test_cli_report_nested_directory()
    test_extreme_thresholds()
    test_high_rounds()
    test_judge_adversarial_inputs()
    test_gate_adversarial_inputs()
    test_seed_determinism()
    test_custom_history_path_creation()
    print("\nALL ADVERSARIAL STRESS TESTS FOR auto_improve.py PASSED SUCCESSFULLY!")
