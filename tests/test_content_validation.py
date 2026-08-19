"""Unit tests for curriculum content validation logic."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_content import validate_content_data, DEFAULT_CONTENT_PATH


class TestContentValidation(unittest.TestCase):
    """Test suite for curriculum validation rules."""

    @classmethod
    def setUpClass(cls):
        with open(DEFAULT_CONTENT_PATH, "r", encoding="utf-8") as f:
            cls.valid_dataset = json.load(f)
        prod_path = Path(__file__).resolve().parent.parent / "content" / "seed_words_prod.json"
        if prod_path.exists():
            with open(prod_path, "r", encoding="utf-8") as f:
                cls.prod_dataset = json.load(f)
        else:
            cls.prod_dataset = None

    def test_real_dev_dataset_passes_validation(self):
        is_valid, passed, errors = validate_content_data(self.valid_dataset)
        self.assertTrue(is_valid, f"Dev dataset failed validation: {[str(e) for e in errors]}")
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(passed), 0)

    def test_real_production_dataset_passes_validation(self):
        if self.prod_dataset is None:
            self.skipTest("Production dataset not yet compiled.")
        is_valid, passed, errors = validate_content_data(self.prod_dataset)
        self.assertTrue(is_valid, f"Production dataset failed validation: {[str(e) for e in errors]}")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(self.prod_dataset["worlds"]), 7)
        self.assertEqual(len(self.prod_dataset["words"]), 1470)

    def test_injected_duplicate_word_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        # Duplicate the first word into the second word's text
        first_word = bad_data["words"][0]["text"]
        bad_data["words"][1]["text"] = first_word

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        error_msgs = [e.message for e in errors]
        self.assertTrue(any("appears multiple times" in msg for msg in error_msgs))

    def test_injected_case_insensitive_duplicate_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        bad_data["words"][1]["text"] = bad_data["words"][0]["text"].upper()

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any(e.check_name == "Duplicate Word" for e in errors))

    def test_missing_meaning_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        bad_data["words"][0]["meaning"] = "  "

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing child-friendly meaning" in e.message for e in errors))

    def test_missing_example_sentence_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        bad_data["words"][0]["example_sentence"] = ""

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing example sentence" in e.message for e in errors))

    def test_missing_pronunciation_hint_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        del bad_data["words"][0]["pronunciation_hint"]

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing pronunciation hint" in e.message for e in errors))

    def test_invalid_difficulty_band_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        bad_data["words"][0]["difficulty_band"] = "super_hard"

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid difficulty band" in e.message for e in errors))

    def test_incorrect_word_count_per_level_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        # Remove one word from Level 1
        removed_word = bad_data["words"].pop(0)

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("has 6 words" in e.message for e in errors))

    def test_invalid_world_reference_flagged(self):
        bad_data = copy.deepcopy(self.valid_dataset)
        bad_data["words"][0]["world_order_index"] = 99

        is_valid, passed, errors = validate_content_data(bad_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid World Reference" in e.check_name for e in errors))


if __name__ == "__main__":
    unittest.main()
