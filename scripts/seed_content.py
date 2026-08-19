"""Developer curriculum seeding script for Pronunciation Adventure.

NOTE: This is an offline developer/admin utility.
It is NEVER imported or executed by the runtime Streamlit application.
At runtime, the application interacts exclusively with Supabase data tables via repositories.

Usage:
    python scripts/seed_content.py [path_to_json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, ConfigurationError
from scripts.developer_client import get_privileged_supabase_client, PrivilegedConfigurationError
from scripts.validate_content import validate_content_data, DEFAULT_CONTENT_PATH


def seed_curriculum_data(json_path: Path, client: Optional[Any] = None) -> bool:
    """
    Idempotently seed worlds, levels, words, and level_words into Supabase.
    Uses the privileged developer client to bypass RLS on content tables.
    """
    print("\n========================================================")
    print("  PRONUNCIATION ADVENTURE - CURRICULUM SEEDER")
    print(f"  Source Dataset: {json_path.name}")
    print("========================================================")

    # 1. Load and parse JSON
    if not json_path.exists():
        print(f"[FAIL] Seed file not found: {json_path}")
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Run Pre-Validation check
    is_valid, passed, errors = validate_content_data(data)
    if not is_valid:
        print("[FAIL] Pre-seed validation failed. Aborting seed operation to protect database integrity.")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[PASS] Pre-seed content validation verified (0 issues).")

    # 3. Obtain Privileged Supabase client
    if client is None:
        try:
            settings = get_settings()
            if not settings.is_configured():
                print("[FAIL] Supabase credentials are not configured in secrets/environment.")
                return False
            client = get_privileged_supabase_client()
        except (ConfigurationError, PrivilegedConfigurationError) as e:
            print(f"\n[FAIL] Privileged authorization required for seeding:\n  {e}\n")
            print("  Note: Normal app execution uses SUPABASE_ANON_KEY.")
            print("  Developer seeding requires SUPABASE_SERVICE_ROLE_KEY in .streamlit/secrets.toml.")
            return False
        except Exception as e:
            print(f"[FAIL] Error initializing privileged client: {e}")
            return False

    raw_worlds = data.get("worlds", [])
    raw_words = data.get("words", [])

    stats = {
        "worlds_upserted": 0,
        "levels_upserted": 0,
        "words_upserted": 0,
        "level_words_linked": 0,
    }

    try:
        # Step A: Batch Upsert Worlds
        world_payloads = [
            {
                "order_index": w["order_index"],
                "name": w["name"],
                "theme_key": w["theme_key"],
                "icon_emoji": w.get("icon_emoji", "✨"),
            }
            for w in raw_worlds
        ]
        client.table("worlds").upsert(world_payloads, on_conflict="order_index").execute()
        w_fetch = client.table("worlds").select("id, order_index").execute()
        world_id_by_order = {row["order_index"]: row["id"] for row in (w_fetch.data or [])}
        stats["worlds_upserted"] = len(world_payloads)
        print(f"[PASS] {len(world_payloads)} worlds upserted.", flush=True)

        # Step B: Batch Upsert Levels
        all_level_payloads = []
        for w in raw_worlds:
            w_order = w["order_index"]
            w_uuid = world_id_by_order.get(w_order)
            if not w_uuid:
                raise RuntimeError(f"Missing world UUID for order_index={w_order}")
            for lvl in w.get("levels", []):
                all_level_payloads.append({
                    "world_id": w_uuid,
                    "order_index": lvl["order_index"],
                    "difficulty_band": lvl["difficulty_band"],
                })

        client.table("levels").upsert(all_level_payloads, on_conflict="world_id,order_index").execute()
        lvl_fetch = client.table("levels").select("id, world_id, order_index").execute()
        world_order_by_id = {v: k for k, v in world_id_by_order.items()}
        level_id_by_coords = {
            (world_order_by_id[row["world_id"]], row["order_index"]): row["id"]
            for row in (lvl_fetch.data or [])
            if row["world_id"] in world_order_by_id
        }
        stats["levels_upserted"] = len(all_level_payloads)
        print(f"[PASS] {len(all_level_payloads)} levels upserted.", flush=True)

        # Step C: Batch Upsert Words (chunked in batches of 200)
        word_payloads = []
        clean_texts = []
        for word_entry in raw_words:
            clean_text = word_entry["text"].strip().lower()
            clean_texts.append(clean_text)
            word_payloads.append({
                "text": clean_text,
                "meaning": word_entry["meaning"].strip(),
                "example_sentence": word_entry["example_sentence"].strip(),
                "pronunciation_hint": word_entry["pronunciation_hint"].strip(),
                "syllable_breakdown": word_entry.get("syllable_breakdown", ""),
                "common_mistake": word_entry.get("common_mistake", ""),
                "image_path": word_entry.get("image_path", ""),
                "image_alt_text": word_entry.get("image_alt_text", ""),
                "difficulty_band": word_entry.get("difficulty_band", "easy"),
            })

        CHUNK_SIZE = 200
        for i in range(0, len(word_payloads), CHUNK_SIZE):
            chunk = word_payloads[i:i + CHUNK_SIZE]
            client.table("words").upsert(chunk, on_conflict="text").execute()
            stats["words_upserted"] += len(chunk)
            print(f"  [Words] {stats['words_upserted']} / {len(word_payloads)} upserted", flush=True)

        # Batch fetch all word UUIDs
        word_id_by_text: Dict[str, str] = {}
        for i in range(0, len(clean_texts), CHUNK_SIZE):
            text_chunk = clean_texts[i:i + CHUNK_SIZE]
            fetch_res = client.table("words").select("id, text").in_("text", text_chunk).execute()
            for row in (fetch_res.data or []):
                word_id_by_text[row["text"]] = row["id"]

        missing_words = [t for t in clean_texts if t not in word_id_by_text]
        if missing_words:
            raise RuntimeError(f"Could not retrieve IDs for {len(missing_words)} words: {missing_words[:5]}")

        # Step D: Batch Upsert level_words mappings (chunked in batches of 200)
        lw_payloads = []
        for word_entry in raw_words:
            clean_text = word_entry["text"].strip().lower()
            w_order = word_entry["world_order_index"]
            l_order = word_entry["level_order_index"]
            order_in_lvl = word_entry["order_index_in_level"]

            level_uuid = level_id_by_coords.get((w_order, l_order))
            word_uuid = word_id_by_text.get(clean_text)

            if not level_uuid or not word_uuid:
                raise RuntimeError(f"Missing UUID reference for word '{clean_text}' (W{w_order}L{l_order})")

            lw_payloads.append({
                "level_id": level_uuid,
                "word_id": word_uuid,
                "order_index": order_in_lvl,
                "is_required": True,
            })

        for i in range(0, len(lw_payloads), CHUNK_SIZE):
            chunk = lw_payloads[i:i + CHUNK_SIZE]
            client.table("level_words").upsert(chunk, on_conflict="level_id,order_index").execute()
            stats["level_words_linked"] += len(chunk)
            print(f"  [Level Words] {stats['level_words_linked']} / {len(lw_payloads)} linked", flush=True)

    except Exception as e:
        print(f"\n[FAIL] Database seeding encountered an error: {e}", flush=True)
        return False

    print("\n--------------------------------------------------------")
    print("  SEEDING COMPLETE — SUMMARY OF PROCESSED ENTITIES")
    print("--------------------------------------------------------")
    print(f"  Worlds Upserted:       {stats['worlds_upserted']} (Unique order_index)")
    print(f"  Levels Upserted:       {stats['levels_upserted']} (Unique world_id, order_index)")
    print(f"  Words Upserted:        {stats['words_upserted']} (Globally unique text)")
    print(f"  Level Words Linked:    {stats['level_words_linked']} (Preserved order_index)")
    print("--------------------------------------------------------\n")
    return True


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTENT_PATH
    success = seed_curriculum_data(target)
    sys.exit(0 if success else 1)
