"""Content validation script for Pronunciation Adventure curriculum datasets.

Usage:
    python scripts/validate_content.py [path_to_json]

Checks:
    - Zero duplicate words (case-insensitive)
    - All required fields present and non-empty
    - Valid world and level assignments
    - Exactly 7 required words per development level
    - Unique order_index_in_level sequence per level
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_PATH = PROJECT_ROOT / "content" / "seed_words_dev.json"
EXPECTED_WORDS_PER_LEVEL = 7


class ContentValidationError:
    def __init__(self, check_name: str, message: str, item_identifier: str = ""):
        self.check_name = check_name
        self.message = message
        self.item_identifier = item_identifier

    def __str__(self) -> str:
        if self.item_identifier:
            return f"[{self.check_name}] ({self.item_identifier}) {self.message}"
        return f"[{self.check_name}] {self.message}"


def validate_content_data(data: Dict[str, Any], expected_words_per_level: int = EXPECTED_WORDS_PER_LEVEL) -> Tuple[bool, List[str], List[ContentValidationError]]:
    """
    Perform deep validation on raw curriculum dictionary.
    
    Returns:
        (is_valid, passed_checks, list_of_errors)
    """
    passed_checks: List[str] = []
    errors: List[ContentValidationError] = []

    worlds = data.get("worlds", [])
    words = data.get("words", [])

    if not worlds:
        errors.append(ContentValidationError("Worlds Structure", "No worlds defined in dataset."))
    if not words:
        errors.append(ContentValidationError("Words Structure", "No words defined in dataset."))
        return False, passed_checks, errors

    # 1. Map valid world/level indices
    valid_world_indices = {w.get("order_index") for w in worlds if isinstance(w, dict) and "order_index" in w}
    valid_world_level_map: Dict[int, set[int]] = {}
    for w in worlds:
        w_idx = w.get("order_index")
        levels = w.get("levels", [])
        valid_world_level_map[w_idx] = {lvl.get("order_index") for lvl in levels if isinstance(lvl, dict) and "order_index" in lvl}

    # 2. Check for duplicate words globally
    seen_words: Dict[str, Dict[str, Any]] = {}
    duplicate_words: List[str] = []
    for entry in words:
        raw_text = entry.get("text", "")
        if not isinstance(raw_text, str) or not raw_text.strip():
            errors.append(ContentValidationError("Word Text", "Word entry has empty or invalid 'text' field.", str(entry)))
            continue
        
        normalized = raw_text.strip().lower()
        if normalized in seen_words:
            prev = seen_words[normalized]
            duplicate_words.append(normalized)
            errors.append(ContentValidationError(
                "Duplicate Word",
                f"Word '{normalized}' appears multiple times (W{prev.get('world_order_index')}L{prev.get('level_order_index')} and W{entry.get('world_order_index')}L{entry.get('level_order_index')}).",
                normalized
            ))
        else:
            seen_words[normalized] = entry

    if not duplicate_words:
        passed_checks.append(f"No duplicate words ({len(seen_words)} unique words verified)")

    # 3. Validate educational fields on each word
    required_str_fields = [
        ("meaning", "Missing child-friendly meaning"),
        ("example_sentence", "Missing example sentence"),
        ("pronunciation_hint", "Missing pronunciation hint"),
        ("image_path", "Missing image path/reference"),
        ("difficulty_band", "Missing difficulty band ('easy'/'medium'/'hard')")
    ]

    missing_field_count = 0
    for entry in words:
        word_text = entry.get("text", "UNKNOWN")
        for field, err_desc in required_str_fields:
            val = entry.get(field)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(ContentValidationError("Required Metadata", f"{err_desc} for word '{word_text}'", word_text))
                missing_field_count += 1

        # Check difficulty_band valid enum
        band = entry.get("difficulty_band")
        if band not in ("easy", "medium", "hard"):
            errors.append(ContentValidationError("Difficulty Band", f"Invalid difficulty band '{band}' for word '{word_text}'. Expected 'easy', 'medium', or 'hard'.", word_text))
            missing_field_count += 1

    if missing_field_count == 0:
        passed_checks.append("All words have complete educational metadata (meaning, sentence, hint, image, difficulty)")

    # 4. Validate hierarchy assignments and word counts per level
    level_word_map: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for entry in words:
        word_text = entry.get("text", "UNKNOWN")
        w_idx = entry.get("world_order_index")
        l_idx = entry.get("level_order_index")

        if w_idx not in valid_world_indices:
            errors.append(ContentValidationError("Invalid World Reference", f"Word '{word_text}' references invalid world_order_index={w_idx}", word_text))
            continue

        valid_levels_for_w = valid_world_level_map.get(w_idx, set())
        if l_idx not in valid_levels_for_w:
            errors.append(ContentValidationError("Invalid Level Reference", f"Word '{word_text}' references invalid level_order_index={l_idx} in World {w_idx}", word_text))
            continue

        key = (w_idx, l_idx)
        if key not in level_word_map:
            level_word_map[key] = []
        level_word_map[key].append(entry)

    # 5. Check exact required count per level and ordering
    count_errors = 0
    ordering_errors = 0
    total_levels_evaluated = 0

    for w in worlds:
        w_idx = w.get("order_index")
        for lvl in w.get("levels", []):
            l_idx = lvl.get("order_index")
            total_levels_evaluated += 1
            key = (w_idx, l_idx)
            words_in_lvl = level_word_map.get(key, [])

            # Check count
            if len(words_in_lvl) != expected_words_per_level:
                errors.append(ContentValidationError(
                    "Level Word Count",
                    f"World {w_idx} Level {l_idx} has {len(words_in_lvl)} words (Expected exactly {expected_words_per_level}).",
                    f"W{w_idx}L{l_idx}"
                ))
                count_errors += 1

            # Check sequence order_index_in_level (1 to N)
            order_indices = [entry.get("order_index_in_level") for entry in words_in_lvl]
            expected_indices = list(range(1, len(words_in_lvl) + 1))
            if sorted(order_indices) != expected_indices:
                errors.append(ContentValidationError(
                    "Word Sequence Order",
                    f"World {w_idx} Level {l_idx} word sequence indices {order_indices} are not a contiguous 1..N sequence.",
                    f"W{w_idx}L{l_idx}"
                ))
                ordering_errors += 1

    if count_errors == 0:
        passed_checks.append(f"All {total_levels_evaluated} levels contain exactly {expected_words_per_level} required words")
    if ordering_errors == 0:
        passed_checks.append("All level word sequence positions (order_index_in_level) are valid and contiguous")

    is_valid = len(errors) == 0
    return is_valid, passed_checks, errors


def run_validation(json_path: Path) -> bool:
    """Run validation from file path and print report."""
    print("\n========================================================")
    print(f"  PRONUNCIATION ADVENTURE - CONTENT VALIDATION")
    print(f"  Target File: {json_path.name}")
    print("========================================================")

    if not json_path.exists():
        print(f"\n❌ FATAL: Content file does not exist at {json_path}")
        return False

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"\n❌ FATAL: JSON Parsing error: {e}")
        return False

    is_valid, passed_checks, errors = validate_content_data(data)

    print("\n--- VALIDATION CHECKS ---")
    for check in passed_checks:
        print(f"  [PASS] {check}")

    if errors:
        print("\n--- VALIDATION FAILURES ---")
        for err in errors:
            print(f"  [FAIL] {err}")

    print("\n--------------------------------------------------------")
    if is_valid:
        print("  OVERALL STATUS: [PASS] (0 issues detected)")
        print("--------------------------------------------------------\n")
        return True
    else:
        print(f"  OVERALL STATUS: [FAIL] ({len(errors)} issue(s) detected)")
        print("--------------------------------------------------------\n")
        return False


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTENT_PATH
    success = run_validation(target)
    sys.exit(0 if success else 1)
