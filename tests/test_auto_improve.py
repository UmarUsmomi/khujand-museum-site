#!/usr/bin/env python3
"""
tests/test_auto_improve.py - Verification suite for Requirement R5 Auto-Improve Engine.

Tests:
- Unit tests for IndependentJudge (4D rubric, anachronism penalties, 3D technical keywords).
- Unit tests for PairwiseBlindGate (double-blind randomization, unblinding, anti-regression threshold, accuracy regression rejection).
- Unit tests for ContentMutator (generation of candidates and strategies).
- Integration tests for AutoImproveEngine (lineage tracking, audit history format).
- CLI invocation tests (flags, dry-run, report export, exit codes).
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

# Add project root to sys.path
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


class TestIndependentJudge(unittest.TestCase):
    def setUp(self):
        self.judge = IndependentJudge()

    def test_rubric_weights_sum_to_one(self):
        weights = self.judge.weights
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        self.assertAlmostEqual(weights["accuracy"], 0.35, places=2)
        self.assertAlmostEqual(weights["register"], 0.25, places=2)
        self.assertAlmostEqual(weights["clarity"], 0.20, places=2)
        self.assertAlmostEqual(weights["technical"], 0.20, places=2)

    def test_evaluate_text_baseline_vs_enriched(self):
        baseline = "Бронзовая скульптура героя в зале музея."
        enriched = (
            "Бронзовая скульптура Тимурмалика (ИНВ-ТМ-0034; высота 3,5 м; автор Д. Рахматов) — "
            "доминанта Центрального купольного зала. Памятник увековечивает оборону Худжандской крепости "
            "в 1219–1220 гг. от войск Чингисхана на реке Сырдарья. В экспозиции представлены средневековые доспехи."
        )
        res_baseline = self.judge.evaluate_text_description(baseline)
        res_enriched = self.judge.evaluate_text_description(enriched)

        self.assertGreater(res_enriched["composite"], res_baseline["composite"])
        self.assertGreater(res_enriched["accuracy"], res_baseline["accuracy"])
        self.assertGreater(res_enriched["register"], res_baseline["register"])
        self.assertGreater(res_enriched["technical"], res_baseline["technical"])

    def test_anachronism_penalty(self):
        clean_text = "Историческая цитадель Худжанда VII–VIII веков."
        anachronistic_text = "Историческая цитадель Худжанда с боевыми танками и пластиковыми геймпадами."

        res_clean = self.judge.evaluate_text_description(clean_text)
        res_anach = self.judge.evaluate_text_description(anachronistic_text)

        self.assertLess(res_anach["accuracy"], res_clean["accuracy"])
        self.assertGreaterEqual(res_anach["breakdown"]["anachronisms_count"], 1)

    def test_informal_slang_penalty(self):
        formal_text = "Монументальная экспозиция древней керамики Согдианы."
        informal_text = "Супер крутая экспозиция древней керамики, настоящий шок и классная вещица!!"

        res_formal = self.judge.evaluate_text_description(formal_text)
        res_informal = self.judge.evaluate_text_description(informal_text)

        self.assertLess(res_informal["register"], res_formal["register"])
        self.assertGreaterEqual(res_informal["breakdown"]["informal_slang_count"], 1)

    def test_evaluate_3d_prompt_parameters(self):
        vague_prompt = "3d model of ancient fortress."
        technical_prompt = (
            "3D procedural model of Khujand Citadel on Syr Darya river. PBR mudbrick walls, "
            "roughness 0.65, normal map bump relief, Three.js WebGL compatible, low-poly budget 22,000 triangles, "
            "3-point studio lighting (3200K key, 5500K fill), dark museum plinth, 60 FPS real-time."
        )

        res_vague = self.judge.evaluate_3d_prompt(vague_prompt)
        res_tech = self.judge.evaluate_3d_prompt(technical_prompt)

        self.assertGreater(res_tech["composite"], res_vague["composite"])
        self.assertGreater(res_tech["technical"], res_vague["technical"])
        self.assertGreater(res_tech["register"], res_vague["register"])

    def test_blind_evaluation_structure(self):
        opt1 = "Текст номер один про согдийский хум."
        opt2 = "Текст номер два про золотой шлем саков."
        blind_res = self.judge.evaluate_blind(opt1, opt2, "descriptions")

        self.assertIn("option_1", blind_res)
        self.assertIn("option_2", blind_res)
        for key in ("accuracy", "register", "clarity", "technical", "composite"):
            self.assertIn(key, blind_res["option_1"])
            self.assertIn(key, blind_res["option_2"])


class TestPairwiseBlindGate(unittest.TestCase):
    def setUp(self):
        self.judge = IndependentJudge()
        self.gate = PairwiseBlindGate(self.judge, threshold=0.03)

    def test_promotion_when_improvement_exceeds_threshold(self):
        champion = "Глиняный кувшин эпохи Согдианы."
        challenger = (
            "Монументальный керамический хум (ИНВ-СМ-4821; обожжённая глина, минеральная охра; VI–IV вв. до н.э.) — "
            "экспонат Зала Древней Согдианы цитадели Худжанда, открытый экспедицией академика Н. Негматова."
        )

        result = self.gate.evaluate_pair(champion, challenger, "descriptions")
        self.assertTrue(result["promoted"])
        self.assertEqual(result["decision"], "PROMOTED")
        self.assertGreaterEqual(result["score_delta"], 0.03)
        self.assertGreaterEqual(result["accuracy_delta"], 0.0)
        self.assertIn("Promoted", result["decision_reason"])
        self.assertTrue(len(result["diff"]) > 0)

    def test_rejection_when_below_threshold(self):
        champion = "Бронзовая статуя Тимурмалика высотой 3,5 метра в центральном зале музея."
        # Minimal change that won't improve score by 3%
        challenger = "Бронзовая статуя Тимурмалика высотой 3,5 метра в центральном зале музея!"

        result = self.gate.evaluate_pair(champion, challenger, "descriptions")
        self.assertFalse(result["promoted"])
        self.assertEqual(result["decision"], "REJECTED")
        self.assertIn("below threshold", result["decision_reason"])

    def test_rejection_when_accuracy_degrades(self):
        champion = (
            "Монументальная бронзовая скульптура Тимурмалика в Худжанде 1219–1220 гг., "
            "героя обороны цитадели от Чингисхана."
        )
        # Higher word count but with anachronism and loss of key historical facts
        challenger = (
            "Красивая современная скульптура воина с танками, геймпадами и пластиковыми деталями, "
            "установленная в каком-то неизвестном веке."
        )

        result = self.gate.evaluate_pair(champion, challenger, "descriptions")
        self.assertFalse(result["promoted"])
        self.assertEqual(result["decision"], "REJECTED")
        self.assertIn("Historical accuracy degraded", result["decision_reason"])

    def test_unblinding_fidelity(self):
        champion = "Описание А"
        challenger = "Описание Б"
        result = self.gate.evaluate_pair(champion, challenger, "descriptions")

        assignment = result["blind_assignment"]
        blind_scores = result["blind_scores"]

        if assignment["option_1"] == "champion":
            self.assertEqual(result["champion_scores"], blind_scores["option_1"])
            self.assertEqual(result["challenger_scores"], blind_scores["option_2"])
        else:
            self.assertEqual(result["champion_scores"], blind_scores["option_2"])
            self.assertEqual(result["challenger_scores"], blind_scores["option_1"])


class TestContentMutator(unittest.TestCase):
    def setUp(self):
        self.mutator = ContentMutator()

    def test_generate_candidate_stages(self):
        target = EXHIBIT_TARGETS["exhibit_timur_malik"]
        baseline = target["baseline"]

        text_r1, strat_r1 = self.mutator.generate_candidate(baseline, "descriptions", 1, target)
        text_r2, strat_r2 = self.mutator.generate_candidate(text_r1, "descriptions", 2, target)

        self.assertNotEqual(text_r1, baseline)
        self.assertNotEqual(text_r2, text_r1)
        self.assertEqual(strat_r1, "curatorial_elevation")
        self.assertEqual(strat_r2, "archaeological_precision")

    def test_generate_adversarial_regression(self):
        text, strat = self.mutator.generate_candidate(
            "Some text", "descriptions", 1, {}, force_regression=True
        )
        self.assertEqual(strat, "adversarial_regression_probe")
        self.assertIn("супер крутая", text)


class TestAutoImproveEngine(unittest.TestCase):
    def test_run_descriptions_task(self):
        engine = AutoImproveEngine(rounds=2, threshold=0.03, dry_run=True, seed=42)
        report = engine.run_optimization(task="descriptions")

        self.assertIn("execution_summary", report)
        self.assertIn("lineage", report)
        summary = report["execution_summary"]
        self.assertEqual(summary["total_targets_processed"], len(EXHIBIT_TARGETS))
        self.assertGreater(summary["total_promotions"], 0)
        self.assertGreater(summary["average_improvement_pct"], 0.0)

        for target_id in EXHIBIT_TARGETS:
            self.assertIn(target_id, report["lineage"])
            target_lineage = report["lineage"][target_id]
            self.assertEqual(len(target_lineage["rounds"]), 2)
            self.assertGreater(
                target_lineage["final_champion"]["scores"]["composite"],
                target_lineage["initial_baseline"]["scores"]["composite"],
            )

    def test_run_3d_prompts_task(self):
        engine = AutoImproveEngine(rounds=2, threshold=0.03, dry_run=True, seed=42)
        report = engine.run_optimization(task="3d-prompts")

        summary = report["execution_summary"]
        self.assertEqual(summary["total_targets_processed"], len(PROMPT_TARGETS))
        self.assertGreater(summary["total_promotions"], 0)

        for target_id in PROMPT_TARGETS:
            self.assertIn(target_id, report["lineage"])

    def test_save_and_verify_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = pathlib.Path(tmpdir) / "test_history.json"
            engine = AutoImproveEngine(rounds=1, threshold=0.03, dry_run=False, seed=1)
            report = engine.run_optimization(task="descriptions")
            engine.save_history(report, test_path)

            self.assertTrue(test_path.exists())
            with open(test_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["version"], "1.0.0")
            self.assertIn("lineage", data)
            self.assertIn("rubric_weights", data)
            self.assertEqual(data["configuration"]["rounds"], 1)


class TestAutoImproveCLI(unittest.TestCase):
    def test_cli_help(self):
        cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "auto_improve.py"), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Khujand Museum GAN-style Auto-Improve Engine", res.stdout)

    def test_cli_dry_run_all(self):
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "auto_improve.py"),
            "--task",
            "all",
            "--rounds",
            "1",
            "--dry-run",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("[DRY-RUN]", res.stdout)
        self.assertIn("Targets evaluated:", res.stdout)

    def test_cli_custom_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = pathlib.Path(tmpdir) / "cli_report.json"
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "auto_improve.py"),
                "--task",
                "descriptions",
                "--rounds",
                "1",
                "--dry-run",
                "--report",
                str(report_file),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(report_file.exists())
            with open(report_file, "r", encoding="utf-8") as f:
                rep = json.load(f)
            self.assertEqual(rep["configuration"]["task"], "descriptions")

    def test_history_file_exists_and_valid(self):
        self.assertTrue(DEFAULT_HISTORY_FILE.exists())
        with open(DEFAULT_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("exhibit_timur_malik", data["lineage"])
        self.assertIn("prompt_timur_malik_statue", data["lineage"])


if __name__ == "__main__":
    unittest.main()
