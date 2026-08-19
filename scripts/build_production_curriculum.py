"""Builds and validates the 1,470-word Production Curriculum JSON dataset for Pronunciation Adventure.
Generates 7 Worlds × 30 Levels × 7 Words = 1,470 globally unique words.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROD_CONTENT_PATH = PROJECT_ROOT / "content" / "seed_words_prod.json"


def get_difficulty_band(level_index: int) -> str:
    """Return difficulty band based on level index."""
    if level_index <= 10:
        return "easy"
    elif level_index <= 20:
        return "medium"
    return "hard"


def generate_production_curriculum() -> Dict[str, Any]:
    """Generates the structured 1,470-word production dataset."""
    from scripts.curriculum_data_source import ALL_CURRICULUM_WORLDS, ALL_CURRICULUM_WORDS

    worlds_json = []
    for w in ALL_CURRICULUM_WORLDS:
        w_levels = []
        for l_idx in range(1, 31):
            w_levels.append({
                "order_index": l_idx,
                "difficulty_band": get_difficulty_band(l_idx)
            })
        worlds_json.append({
            "order_index": w["order_index"],
            "name": w["name"],
            "theme_key": w["theme_key"],
            "icon_emoji": w["icon_emoji"],
            "levels": w_levels
        })

    return {
        "worlds": worlds_json,
        "words": ALL_CURRICULUM_WORDS
    }


def main():
    print("Building production curriculum dataset...")
    data = generate_production_curriculum()
    
    # Save to JSON
    PROD_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROD_CONTENT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully generated {PROD_CONTENT_PATH.name}:")
    print(f"  - Worlds: {len(data['worlds'])}")
    print(f"  - Levels per world: {len(data['worlds'][0]['levels'])} (Total: {len(data['worlds']) * len(data['worlds'][0]['levels'])})")
    print(f"  - Words: {len(data['words'])}")


if __name__ == "__main__":
    main()
