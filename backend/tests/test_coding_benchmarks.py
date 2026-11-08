import gzip
import hashlib
import json
import os
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from llm_rankings.coding_benchmarks import (
    EffortScore,
    LiveCodingRow,
    apply_coding_benchmarks,
    coding_for_slug,
    coding_percent,
    copy_stored_coding,
    decrypt_frontier_blob,
    fetch_needed,
    frontier_scores,
    matching_effort,
    parse_frontier_manifest,
    read_coding_benchmark_error,
    terminal_rows,
)
from llm_rankings.combined_models import CombinedModel
from llm_rankings.database import combined_model_from_row
from llm_rankings.or_models import OpenRouterModel


def _model(model_id: str, intelligence: float | None = None, coding: float | None = None) -> CombinedModel:
    return CombinedModel(
        id=model_id,
        input_modalities=[],
        output_modalities=[],
        benchmark_or_intelligence_index=intelligence,
        benchmark_coding=coding,
    )


def _encrypt(payload: dict, key: bytes) -> bytes:
    iv = hashlib.sha256(key).digest()[:12]
    blob = gzip.compress(json.dumps(payload).encode())
    return AESGCM(key).encrypt(iv, blob, None)


class CodingScoreTests(unittest.TestCase):
    def test_opus_blend(self):
        # FrontierCode 46.4 and Terminal-Bench 59.6 → 51.7
        self.assertEqual(coding_percent(0.464, 0.595959595959596), 51.7)

    def test_both_inputs_required(self):
        efforts = {
            "anthropic/claude-opus-5.5": [
                EffortScore("aa-max", 59.1, 0.596),
            ]
        }
        self.assertIsNone(coding_for_slug("anthropic/claude-opus-5.5", 59.1, efforts, {}))
        self.assertIsNone(
            coding_for_slug(
                "anthropic/claude-opus-5.5",
                59.1,
                {"anthropic/claude-opus-5.5": [EffortScore("aa-max", 59.1, None)]},
                {"aa-max": 0.464},
            )
        )

    def test_effort_match_and_tie(self):
        rows = [
            EffortScore("low", 57.4, 0.50),
            EffortScore("lower-tied", 59.06, 0.70),
            EffortScore("higher-tied", 59.14, 0.40),
        ]
        chosen = matching_effort(rows, 59.1)
        self.assertEqual(chosen.aa_id, "higher-tied")
        tied = [
            EffortScore("weaker-bench", 59.1, 0.40),
            EffortScore("stronger-bench", 59.1, 0.70),
        ]
        self.assertEqual(matching_effort(tied, 59.1).aa_id, "stronger-bench")
        self.assertIsNone(matching_effort(rows, None))
        self.assertEqual(coding_for_slug("slug", 59.1, {"slug": rows}, {"higher-tied": 0.464}), 43.8)

    def test_fetch_decision(self):
        live = [LiveCodingRow("a", 59.1, 51.7)]
        same = [_model("a", 40.0)]
        self.assertFalse(fetch_needed(live, same, coding_column_present=True, retry_empty_failure=False))
        self.assertTrue(
            fetch_needed(
                live,
                [_model("a", 59.1), _model("b", 10)],
                coding_column_present=True,
                retry_empty_failure=False,
            )
        )
        self.assertTrue(
            fetch_needed(
                [LiveCodingRow("a", None, None)],
                [_model("a", 59.1)],
                coding_column_present=True,
                retry_empty_failure=False,
            )
        )
        self.assertTrue(fetch_needed([], [_model("a", 59.1)], coding_column_present=False, retry_empty_failure=False))
        self.assertTrue(
            fetch_needed(
                [LiveCodingRow("a", 59.1, None)],
                [_model("a", 59.1)],
                coding_column_present=True,
                retry_empty_failure=True,
            )
        )

    def test_manifest_and_decrypt(self):
        escaped = r"\"manifest\":{\"path\":\"/data/abc.txt\",\"key\":\"00112233445566778899aabbccddeeff\"}"
        raw = '{"manifest":{"path":"/data/abc.txt","key":"00112233445566778899aabbccddeeff"}}'
        self.assertEqual(
            parse_frontier_manifest(escaped),
            ("https://artificialanalysis.ai/data/abc.txt", "00112233445566778899aabbccddeeff"),
        )
        self.assertEqual(parse_frontier_manifest(raw)[0], "https://artificialanalysis.ai/data/abc.txt")
        key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
        blob = _encrypt(
            {
                "models": [
                    {"id": "keep", "frontierCode20": 0.464},
                    {"id": "drop", "frontierCode20": 0.1},
                ]
            },
            key,
        )
        payload = decrypt_frontier_blob(blob, key.hex())
        self.assertEqual(frontier_scores(payload, {"keep"}), {"keep": 0.464})

    def test_terminal_rows(self):
        payload = {
            "data": [
                {
                    "aa_id": "aa-max",
                    "permaslug": "anthropic/claude-opus-5.5",
                    "benchmark_data": {
                        "evaluations": {
                            "artificial_analysis_intelligence_index": 59.1,
                            "terminalbench_v4_0": 0.596,
                        }
                    },
                }
            ]
        }
        rows = terminal_rows(payload)
        self.assertEqual(rows["anthropic/claude-opus-5.5"][0].intelligence, 59.1)


class ApplyCodingTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path("/tmp") / f"coding-benchmarks-{uuid4().hex}"
        self.data_dir.mkdir()
        self._previous = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = str(self.data_dir)

    def tearDown(self):
        if self._previous is None:
            os.environ.pop("DATA_DIR", None)
        else:
            os.environ["DATA_DIR"] = self._previous
        for path in sorted(self.data_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            else:
                path.rmdir()
        self.data_dir.rmdir()

    def _write_live(self, columns: str, row: tuple) -> None:
        connection = sqlite3.connect(self.data_dir / "database.db")
        connection.execute(f"CREATE TABLE models ({columns})")
        placeholders = ",".join("?" for _ in row)
        connection.execute(f"INSERT INTO models VALUES ({placeholders})", row)
        connection.commit()
        connection.close()

    def test_skip_copies_stored_score(self):
        self._write_live(
            "id TEXT, benchmark_or_intelligence_index REAL, benchmark_coding REAL",
            ("a", 59.1, 51.7),
        )
        models = [_model("a", 40.0)]
        with patch("llm_rankings.coding_benchmarks._get_json") as get_json:
            apply_coding_benchmarks(models, [])
        get_json.assert_not_called()
        self.assertEqual(models[0].benchmark_coding, 51.7)
        self.assertIsNone(read_coding_benchmark_error())

    def test_failure_keeps_stored_score_and_records_error(self):
        self._write_live(
            "id TEXT, benchmark_or_intelligence_index REAL, benchmark_coding REAL",
            ("a", 59.1, 51.7),
        )
        models = [_model("a", 59.1), _model("b", 10)]
        with patch("llm_rankings.coding_benchmarks._get_json", side_effect=ValueError("down")):
            apply_coding_benchmarks(models, [])
        self.assertEqual(models[0].benchmark_coding, 51.7)
        self.assertIsNone(models[1].benchmark_coding)
        self.assertEqual(read_coding_benchmark_error(), "Coding benchmark fetch failed.")

    def test_success_replaces_scores_and_clears_error(self):
        self._write_live("id TEXT, benchmark_or_intelligence_index REAL", ("a", None))
        (self.data_dir / "cache" / "openrouter").mkdir(parents=True)
        (self.data_dir / "cache" / "openrouter" / "coding_benchmark_error.json").write_text(
            '{"error": "Coding benchmark fetch failed."}\n'
        )
        models = [_model("a", 59.1)]
        or_model = OpenRouterModel.model_construct(id="a", canonical_slug="anthropic/claude-opus-5.5")
        terminal = {
            "data": [
                {
                    "aa_id": "aa-max",
                    "permaslug": "anthropic/claude-opus-5.5",
                    "benchmark_data": {
                        "evaluations": {
                            "artificial_analysis_intelligence_index": 59.1,
                            "terminalbench_v4_0": 0.595959595959596,
                        }
                    },
                }
            ]
        }
        key = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")
        blob = _encrypt({"models": [{"id": "aa-max", "frontierCode20": 0.464}]}, key)
        html = r"\"manifest\":{\"path\":\"/data/abc.txt\",\"key\":\"" + key.hex() + r"\"}"
        with (
            patch("llm_rankings.coding_benchmarks._get_json", return_value=terminal),
            patch("llm_rankings.coding_benchmarks._get_text", return_value=html),
            patch("llm_rankings.coding_benchmarks._get_bytes", return_value=blob),
        ):
            apply_coding_benchmarks(models, [or_model])
        self.assertEqual(models[0].benchmark_coding, 51.7)
        self.assertIsNone(read_coding_benchmark_error())


class RowLoadTests(unittest.TestCase):
    def test_old_snapshot_ignores_dropped_columns(self):
        model = combined_model_from_row(
            {
                "id": "a",
                "input_modalities": '["text"]',
                "output_modalities": '["text"]',
                "is_open_weights": 1,
                "benchmark_or_intelligence_index": 59.1,
                "benchmark_or_coding_index": 12,
                "benchmark_or_agentic_index": 8,
            }
        )
        self.assertEqual(model.id, "a")
        self.assertTrue(model.is_open_weights)
        self.assertIsNone(model.benchmark_coding)
        self.assertEqual(model.benchmark_or_intelligence_index, 59.1)


class CopyTests(unittest.TestCase):
    def test_copy_leaves_unknown_ids_empty(self):
        models = [_model("new", 1)]
        copy_stored_coding(models, [LiveCodingRow("old", 1, 20)])
        self.assertIsNone(models[0].benchmark_coding)
