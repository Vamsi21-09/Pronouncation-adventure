"""Repository for accessing curriculum content (worlds, levels, words) in Supabase with caching."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from supabase import Client
from repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Process-level memory caches for static curriculum (default client only)
_cached_worlds: Optional[List[Dict[str, Any]]] = None
_cached_levels_by_world: Dict[str, List[Dict[str, Any]]] = {}
_cached_words_by_level: Dict[str, List[Dict[str, Any]]] = {}


class ContentRepositoryError(Exception):
    """Base exception for content query failures."""
    pass


class ContentRepository:
    """Encapsulates all database reads for curriculum worlds, levels, and words."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        return get_supabase_client()

    def get_all_worlds(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all worlds ordered by order_index.
        
        Returns:
            List of world dictionaries.
        """
        global _cached_worlds
        if self._client is None and use_cache and _cached_worlds is not None:
            return _cached_worlds

        try:
            response = self.client.table("worlds").select("*").order("order_index").execute()
            data = response.data or []
            if self._client is None and data:
                _cached_worlds = data
            return data
        except Exception as e:
            if self._client is None and _cached_worlds is not None:
                return _cached_worlds
            logger.error("Failed to query worlds: %s", e)
            raise ContentRepositoryError(f"Error querying worlds: {e}") from e

    def get_world_by_order_index(self, order_index: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific world by its order index (1..7)."""
        worlds = self.get_all_worlds()
        for w in worlds:
            if w.get("order_index") == order_index:
                return w

        try:
            response = self.client.table("worlds").select("*").eq("order_index", order_index).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error("Failed to query world by order_index=%s: %s", order_index, e)
            raise ContentRepositoryError(f"Error querying world: {e}") from e

    def get_levels_for_world(self, world_id: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch all levels in a specific world ordered by order_index.
        
        Args:
            world_id: The UUID of the world.
            
        Returns:
            List of level dictionaries.
        """
        global _cached_levels_by_world
        if self._client is None and use_cache and world_id in _cached_levels_by_world:
            return _cached_levels_by_world[world_id]

        try:
            response = (
                self.client.table("levels")
                .select("*")
                .eq("world_id", world_id)
                .order("order_index")
                .execute()
            )
            data = response.data or []
            if self._client is None and data:
                _cached_levels_by_world[world_id] = data
            return data
        except Exception as e:
            if self._client is None and world_id in _cached_levels_by_world:
                return _cached_levels_by_world[world_id]
            logger.error("Failed to query levels for world_id=%s: %s", world_id, e)
            raise ContentRepositoryError(f"Error querying levels: {e}") from e

    def get_words_for_level(self, level_id: str, required_only: bool = True, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch words assigned to a specific level, ordered by their sequence within the level.
        
        Args:
            level_id: The UUID of the level.
            required_only: If True, filters out optional/bonus words.
            
        Returns:
            List of dictionaries containing word details combined with level_words ordering.
        """
        global _cached_words_by_level
        cache_key = f"{level_id}_{required_only}"
        if self._client is None and use_cache and cache_key in _cached_words_by_level:
            return _cached_words_by_level[cache_key]

        try:
            query = (
                self.client.table("level_words")
                .select("order_index, is_required, words(*)")
                .eq("level_id", level_id)
            )
            if required_only:
                query = query.eq("is_required", True)

            response = query.order("order_index").execute()
            results: List[Dict[str, Any]] = []

            for row in (response.data or []):
                word_obj = row.get("words")
                if word_obj:
                    # Flatten order_index and is_required onto word dictionary
                    merged = dict(word_obj)
                    merged["order_index_in_level"] = row.get("order_index")
                    merged["is_required"] = row.get("is_required", True)
                    results.append(merged)

            if self._client is None and results:
                _cached_words_by_level[cache_key] = results
            return results
        except Exception as e:
            if self._client is None and cache_key in _cached_words_by_level:
                return _cached_words_by_level[cache_key]
            logger.error("Failed to query words for level_id=%s: %s", level_id, e)
            raise ContentRepositoryError(f"Error querying words for level: {e}") from e


def get_content_repository() -> ContentRepository:
    """Helper factory for ContentRepository."""
    return ContentRepository()


def clear_content_cache() -> None:
    """Clear memory caches for testing or post-seeding."""
    global _cached_worlds, _cached_levels_by_world, _cached_words_by_level
    _cached_worlds = None
    _cached_levels_by_world = {}
    _cached_words_by_level = {}
