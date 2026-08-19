"""Unit tests for ContentRepository queries and joins."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from repositories.content_repo import ContentRepository, ContentRepositoryError


class TestContentRepository(unittest.TestCase):
    """Test suite for ContentRepository data access methods."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.repo = ContentRepository(client=self.mock_client)

    def test_get_all_worlds_success(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {"id": "w-1", "order_index": 1, "name": "Village", "theme_key": "village"},
            {"id": "w-2", "order_index": 2, "name": "Forest", "theme_key": "forest"},
        ])
        self.mock_client.table.return_value = mock_query

        worlds = self.repo.get_all_worlds()
        self.assertEqual(len(worlds), 2)
        self.assertEqual(worlds[0]["name"], "Village")
        self.assertEqual(worlds[1]["name"], "Forest")

    def test_get_levels_for_world_success(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[
            {"id": "lvl-1", "world_id": "w-1", "order_index": 1, "difficulty_band": "easy"},
            {"id": "lvl-2", "world_id": "w-1", "order_index": 2, "difficulty_band": "medium"},
            {"id": "lvl-3", "world_id": "w-1", "order_index": 3, "difficulty_band": "hard"},
        ])
        self.mock_client.table.return_value = mock_query

        levels = self.repo.get_levels_for_world("w-1")
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels[0]["difficulty_band"], "easy")

    def test_get_words_for_level_ordering_and_flattening(self):
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query

        # Mock join response from level_words with nested words(*)
        mock_query.execute.return_value = MagicMock(data=[
            {
                "order_index": 1,
                "is_required": True,
                "words": {
                    "id": "word-1",
                    "text": "house",
                    "meaning": "A dwelling",
                    "pronunciation_hint": "HOWSS"
                }
            },
            {
                "order_index": 2,
                "is_required": True,
                "words": {
                    "id": "word-2",
                    "text": "market",
                    "meaning": "A shopping area",
                    "pronunciation_hint": "MAHR-kit"
                }
            }
        ])
        self.mock_client.table.return_value = mock_query

        words = self.repo.get_words_for_level("lvl-1", required_only=True)
        self.assertEqual(len(words), 2)
        self.assertEqual(words[0]["text"], "house")
        self.assertEqual(words[0]["order_index_in_level"], 1)
        self.assertEqual(words[1]["text"], "market")
        self.assertEqual(words[1]["order_index_in_level"], 2)

    def test_get_words_for_level_error_handling(self):
        mock_query = MagicMock()
        mock_query.select.side_effect = Exception("DB Connection Timeout")
        self.mock_client.table.return_value = mock_query

        with self.assertRaises(ContentRepositoryError):
            self.repo.get_words_for_level("lvl-1")


if __name__ == "__main__":
    unittest.main()
