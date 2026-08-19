"""Comprehensive Production Curriculum Compiler for Pronunciation Adventure.
Generates exactly 7 Worlds × 30 Levels × 7 Words = 1,470 globally unique vocabulary words.
Saves output to content/seed_words_prod.json.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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

def make_word(
    text: str,
    meaning: str,
    sentence: str,
    hint: str,
    syllables: str,
    mistake: str,
    alt: str,
    w_idx: int,
    l_idx: int,
    pos_idx: int
) -> dict:
    diff = "easy" if l_idx <= 10 else ("medium" if l_idx <= 20 else "hard")
    norm_text = text.lower().strip()
    return {
        "text": norm_text,
        "meaning": meaning.strip(),
        "example_sentence": sentence.strip(),
        "pronunciation_hint": hint.strip(),
        "syllable_breakdown": syllables.strip(),
        "common_mistake": mistake.strip(),
        "image_path": f"words/{norm_text}.webp",
        "image_alt_text": alt.strip(),
        "difficulty_band": diff,
        "world_order_index": w_idx,
        "level_order_index": l_idx,
        "order_index_in_level": pos_idx
    }
