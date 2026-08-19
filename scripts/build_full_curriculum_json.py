"""Generates the full 1,470-word Production Curriculum for Pronunciation Adventure.
Contains 7 worlds × 30 levels × 7 words = 1,470 globally unique, themed words with rich educational metadata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
PROD_JSON_PATH = PROJECT_ROOT / "content" / "seed_words_prod.json"

WORLDS_METADATA = [
    {"order_index": 1, "name": "Village", "theme_key": "village", "icon_emoji": "🏡"},
    {"order_index": 2, "name": "Forest", "theme_key": "forest", "icon_emoji": "🌲"},
    {"order_index": 3, "name": "Mountain", "theme_key": "mountain", "icon_emoji": "🏔️"},
    {"order_index": 4, "name": "Ocean", "theme_key": "ocean", "icon_emoji": "🌊"},
    {"order_index": 5, "name": "Desert", "theme_key": "desert", "icon_emoji": "🏜️"},
    {"order_index": 6, "name": "Sky", "theme_key": "sky", "icon_emoji": "☁️"},
    {"order_index": 7, "name": "Crystal", "theme_key": "crystal", "icon_emoji": "💎"},
]

# Curated word banks per world: 30 levels of 7 unique words each (210 words per world, 1,470 words total)
# Each entry: (text, meaning, sentence, hint, syllables, mistake, alt)

from scripts.world1_words import WORLD_1_LEVELS
from scripts.world2_words import WORLD_2_LEVELS
from scripts.world3_words import WORLD_3_LEVELS
from scripts.world4_words import WORLD_4_LEVELS
from scripts.world5_words import WORLD_5_LEVELS
from scripts.world6_words import WORLD_6_LEVELS
from scripts.world7_words import WORLD_7_LEVELS


def build_curriculum():
    all_raw_worlds = [
        (1, WORLD_1_LEVELS),
        (2, WORLD_2_LEVELS),
        (3, WORLD_3_LEVELS),
        (4, WORLD_4_LEVELS),
        (5, WORLD_5_LEVELS),
        (6, WORLD_6_LEVELS),
        (7, WORLD_7_LEVELS),
    ]

    seen_words = set()
    formatted_words = []
    worlds_json = []

    for w_meta in WORLDS_METADATA:
        w_idx = w_meta["order_index"]
        w_levels = []
        for l_idx in range(1, 31):
            band = "easy" if l_idx <= 10 else ("medium" if l_idx <= 20 else "hard")
            w_levels.append({
                "order_index": l_idx,
                "difficulty_band": band
            })
        worlds_json.append({
            "order_index": w_idx,
            "name": w_meta["name"],
            "theme_key": w_meta["theme_key"],
            "icon_emoji": w_meta["icon_emoji"],
            "levels": w_levels
        })

    for w_idx, w_data in all_raw_worlds:
        assert len(w_data) == 30, f"World {w_idx} must have exactly 30 levels, got {len(w_data)}"
        for l_idx, level_words in enumerate(w_data, start=1):
            assert len(level_words) == 7, f"World {w_idx} Level {l_idx} must have exactly 7 words, got {len(level_words)}"
            band = "easy" if l_idx <= 10 else ("medium" if l_idx <= 20 else "hard")
            for pos_idx, w_item in enumerate(level_words, start=1):
                text, meaning, sentence, hint, syllables, mistake, alt = w_item
                norm_text = text.lower().strip()
                assert norm_text not in seen_words, f"Duplicate word found: '{norm_text}' in W{w_idx}L{l_idx}"
                seen_words.add(norm_text)

                formatted_words.append({
                    "text": norm_text,
                    "meaning": meaning.strip(),
                    "example_sentence": sentence.strip(),
                    "pronunciation_hint": hint.strip(),
                    "syllable_breakdown": syllables.strip(),
                    "common_mistake": mistake.strip(),
                    "image_path": f"words/{norm_text}.webp",
                    "image_alt_text": alt.strip(),
                    "difficulty_band": band,
                    "world_order_index": w_idx,
                    "level_order_index": l_idx,
                    "order_index_in_level": pos_idx
                })

    assert len(formatted_words) == 1470, f"Expected 1470 words, got {len(formatted_words)}"

    dataset = {
        "worlds": worlds_json,
        "words": formatted_words
    }

    PROD_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROD_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print("========================================================")
    print(f"  PRODUCTION CURRICULUM GENERATED SUCCESSFULLY")
    print(f"  Target File: {PROD_JSON_PATH}")
    print(f"  Worlds: {len(worlds_json)}")
    print(f"  Total Levels: {len(worlds_json) * 30} (30 per world)")
    print(f"  Total Required Words: {len(formatted_words)} (7 per level)")
    print(f"  Unique Words: {len(seen_words)}")
    print("========================================================")


if __name__ == "__main__":
    build_curriculum()
