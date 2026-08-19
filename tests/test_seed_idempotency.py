"""Unit tests verifying seeder idempotency and relational integrity."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from scripts.seed_content import seed_curriculum_data, DEFAULT_CONTENT_PATH


class TestSeedIdempotency(unittest.TestCase):
    """Verify that multiple seed executions produce identical, non-duplicated database state."""

    def setUp(self):
        # Simulated database storage tables
        self.db_worlds: dict[int, dict] = {}
        self.db_levels: dict[tuple[str, int], dict] = {}
        self.db_words: dict[str, dict] = {}
        self.db_level_words: dict[tuple[str, str], dict] = {}

        self.mock_client = MagicMock()

        def mock_table(name: str):
            query = MagicMock()

            if name == "worlds":
                def mock_upsert(payload, on_conflict=None):
                    items = payload if isinstance(payload, list) else [payload]
                    for item in items:
                        key = item["order_index"]
                        if key not in self.db_worlds:
                            self.db_worlds[key] = dict(item, id=f"world-{key}")
                        else:
                            self.db_worlds[key].update(item)
                    return MagicMock()

                def mock_select(fields):
                    sq = MagicMock()
                    sq.execute.return_value = MagicMock(data=list(self.db_worlds.values()))
                    def mock_eq(col, val):
                        res = MagicMock()
                        if col == "order_index":
                            record = self.db_worlds.get(val)
                            res.execute.return_value = MagicMock(data=[record] if record else [])
                        return res
                    sq.eq = mock_eq
                    return sq

                query.upsert = mock_upsert
                query.select = mock_select

            elif name == "levels":
                def mock_upsert(payload, on_conflict=None):
                    items = payload if isinstance(payload, list) else [payload]
                    for item in items:
                        key = (item["world_id"], item["order_index"])
                        if key not in self.db_levels:
                            self.db_levels[key] = dict(item, id=f"lvl-{item['world_id']}-{item['order_index']}")
                        else:
                            self.db_levels[key].update(item)
                    return MagicMock()

                def mock_select(fields):
                    sq = MagicMock()
                    sq.execute.return_value = MagicMock(data=list(self.db_levels.values()))
                    def mock_eq1(col1, val1):
                        sq2 = MagicMock()
                        def mock_eq2(col2, val2):
                            res = MagicMock()
                            key = (val1, val2)
                            record = self.db_levels.get(key)
                            res.execute.return_value = MagicMock(data=[record] if record else [])
                            return res
                        sq2.eq = mock_eq2
                        return sq2
                    sq.eq = mock_eq1
                    return sq

                query.upsert = mock_upsert
                query.select = mock_select

            elif name == "words":
                def mock_upsert(payload, on_conflict=None):
                    items = payload if isinstance(payload, list) else [payload]
                    for item in items:
                        key = item["text"]
                        if key not in self.db_words:
                            self.db_words[key] = dict(item, id=f"word-{key}")
                        else:
                            self.db_words[key].update(item)
                    return MagicMock()

                def mock_select(fields):
                    sq = MagicMock()
                    def mock_eq(col, val):
                        res = MagicMock()
                        if col == "text":
                            record = self.db_words.get(val)
                            res.execute.return_value = MagicMock(data=[record] if record else [])
                        return res
                    def mock_in(col, val_list):
                        res = MagicMock()
                        if col == "text":
                            records = [self.db_words[v] for v in val_list if v in self.db_words]
                            res.execute.return_value = MagicMock(data=records)
                        return res
                    sq.eq = mock_eq
                    sq.in_ = mock_in
                    return sq

                query.upsert = mock_upsert
                query.select = mock_select

            elif name == "level_words":
                def mock_upsert(payload, on_conflict=None):
                    items = payload if isinstance(payload, list) else [payload]
                    for item in items:
                        key = (item["level_id"], item["order_index"])
                        if key not in self.db_level_words:
                            self.db_level_words[key] = dict(item, id=f"lw-{key[0]}-{key[1]}")
                        else:
                            self.db_level_words[key].update(item)
                    return MagicMock()

                query.upsert = mock_upsert

            return query

        self.mock_client.table = mock_table

    def test_idempotent_seeding_multiple_runs(self):
        # First execution with dev dataset
        success_1 = seed_curriculum_data(DEFAULT_CONTENT_PATH, client=self.mock_client)
        self.assertTrue(success_1)

        worlds_run1 = len(self.db_worlds)
        levels_run1 = len(self.db_levels)
        words_run1 = len(self.db_words)
        lw_run1 = len(self.db_level_words)

        self.assertEqual(worlds_run1, 2)
        self.assertEqual(levels_run1, 6)
        self.assertEqual(words_run1, 42)
        self.assertEqual(lw_run1, 42)

        # Second execution (verifying idempotency)
        success_2 = seed_curriculum_data(DEFAULT_CONTENT_PATH, client=self.mock_client)
        self.assertTrue(success_2)

        self.assertEqual(len(self.db_worlds), worlds_run1)
        self.assertEqual(len(self.db_levels), levels_run1)
        self.assertEqual(len(self.db_words), words_run1)
        self.assertEqual(len(self.db_level_words), lw_run1)

    def test_production_dataset_seeding(self):
        from pathlib import Path
        prod_path = Path(__file__).resolve().parent.parent / "content" / "seed_words_prod.json"
        if not prod_path.exists():
            self.skipTest("Production dataset not present.")

        # Seed full production curriculum
        success = seed_curriculum_data(prod_path, client=self.mock_client)
        self.assertTrue(success)
        self.assertEqual(len(self.db_worlds), 7)
        self.assertEqual(len(self.db_levels), 210)
        self.assertEqual(len(self.db_words), 1470)
        self.assertEqual(len(self.db_level_words), 1470)

        # Repeat to verify idempotency on full 1,470-word curriculum
        success_repeat = seed_curriculum_data(prod_path, client=self.mock_client)
        self.assertTrue(success_repeat)
        self.assertEqual(len(self.db_worlds), 7)
        self.assertEqual(len(self.db_levels), 210)
        self.assertEqual(len(self.db_words), 1470)
        self.assertEqual(len(self.db_level_words), 1470)


if __name__ == "__main__":
    unittest.main()
