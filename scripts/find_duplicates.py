"""Checks for duplicates across all world files and suggests unique alternatives."""
from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.world1_words import WORLD_1_LEVELS
from scripts.world2_words import WORLD_2_LEVELS
from scripts.world3_words import WORLD_3_LEVELS
from scripts.world4_words import WORLD_4_LEVELS
from scripts.world5_words import WORLD_5_LEVELS
from scripts.world6_words import WORLD_6_LEVELS
from scripts.world7_words import WORLD_7_LEVELS

all_raw_worlds = [
    (1, WORLD_1_LEVELS),
    (2, WORLD_2_LEVELS),
    (3, WORLD_3_LEVELS),
    (4, WORLD_4_LEVELS),
    (5, WORLD_5_LEVELS),
    (6, WORLD_6_LEVELS),
    (7, WORLD_7_LEVELS),
]

word_locations = defaultdict(list)
total_words = 0

for w_idx, w_data in all_raw_worlds:
    for l_idx, level in enumerate(w_data, start=1):
        for pos_idx, w_item in enumerate(level, start=1):
            total_words += 1
            word_text = w_item[0].lower().strip()
            word_locations[word_text].append((w_idx, l_idx, pos_idx))

duplicates = {w: locs for w, locs in word_locations.items() if len(locs) > 1}

print(f"Total words scanned: {total_words}")
print(f"Unique words: {len(word_locations)}")
print(f"Duplicate words found: {len(duplicates)}")

for w, locs in sorted(duplicates.items()):
    loc_str = ", ".join([f"W{w_i}L{l_i}P{p_i}" for w_i, l_i, p_i in locs])
    print(f"  - '{w}' ({len(locs)} times): {loc_str}")
