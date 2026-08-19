"""Script to assemble the complete 1,470 unique word vocabulary entries across 7 worlds and 30 levels."""
from __future__ import annotations

import json
from pathlib import Path

# Worlds definition
WORLDS = [
    {"order_index": 1, "name": "Village", "theme_key": "village", "icon_emoji": "🏡"},
    {"order_index": 2, "name": "Forest", "theme_key": "forest", "icon_emoji": "🌲"},
    {"order_index": 3, "name": "Mountain", "theme_key": "mountain", "icon_emoji": "🏔️"},
    {"order_index": 4, "name": "Ocean", "theme_key": "ocean", "icon_emoji": "🌊"},
    {"order_index": 5, "name": "Desert", "theme_key": "desert", "icon_emoji": "🏜️"},
    {"order_index": 6, "name": "Sky", "theme_key": "sky", "icon_emoji": "☁️"},
    {"order_index": 7, "name": "Crystal", "theme_key": "crystal", "icon_emoji": "💎"},
]

def make_word_entry(
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
    return {
        "text": text.lower().strip(),
        "meaning": meaning.strip(),
        "example_sentence": sentence.strip(),
        "pronunciation_hint": hint.strip(),
        "syllable_breakdown": syllables.strip(),
        "common_mistake": mistake.strip(),
        "image_path": f"words/{text.lower().strip()}.webp",
        "image_alt_text": alt.strip(),
        "difficulty_band": diff,
        "world_order_index": w_idx,
        "level_order_index": l_idx,
        "order_index_in_level": pos_idx
    }
