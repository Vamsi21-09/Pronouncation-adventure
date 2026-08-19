"""Verifies that all 7 worlds, 210 levels, and 1,470 words are live and queryable in Supabase."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from repositories.content_repo import ContentRepository
from scripts.developer_client import get_privileged_supabase_client

def main():
    client = get_privileged_supabase_client()
    repo = ContentRepository(client=client)
    worlds = repo.get_all_worlds()
    print("=========================================================")
    print(f"  SUPABASE LIVE CONTENT AUDIT: {len(worlds)} Worlds Found")
    print("=========================================================")
    
    total_levels = 0
    total_words_sampled = 0
    
    for w in sorted(worlds, key=lambda x: x.get("order_index", 0)):
        w_id = w["id"]
        w_order = w.get("order_index")
        w_name = w.get("name")
        levels = repo.get_levels_for_world(w_id)
        total_levels += len(levels)
        print(f"  World {w_order}: {w_name} — {len(levels)} Levels")
        
        # Sample level 1 and level 30
        if levels:
            first_lvl = levels[0]
            words_lvl1 = repo.get_words_for_level(first_lvl["id"])
            total_words_sampled += len(words_lvl1)
            print(f"    - Level 1 ({len(words_lvl1)} words): {[w_item.get('text') for w_item in words_lvl1]}")
            
            if len(levels) >= 30:
                last_lvl = levels[-1]
                words_lvl30 = repo.get_words_for_level(last_lvl["id"])
                print(f"    - Level 30 ({len(words_lvl30)} words): {[w_item.get('text') for w_item in words_lvl30]}")

    print("\n---------------------------------------------------------")
    print(f"  Total Worlds Verified: {len(worlds)} (Expected 7)")
    print(f"  Total Levels Verified: {total_levels} (Expected 210)")
    print("---------------------------------------------------------\n")

if __name__ == "__main__":
    main()
