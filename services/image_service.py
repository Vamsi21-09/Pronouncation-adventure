"""Service for resolving, caching, and safely displaying word images."""
from __future__ import annotations

import html
import logging
from pathlib import Path
from typing import Optional
import streamlit as st

from config.settings import get_settings, ConfigurationError

logger = logging.getLogger(__name__)
BUCKET_NAME = "word-images"


class ImageService:
    """Handles resolution of storage paths to public CDN URLs and fallback rendering."""

    @staticmethod
    def get_public_url(image_path: Optional[str]) -> Optional[str]:
        """
        Resolve a relative image_path (e.g. 'words/garden.webp') to a public Supabase Storage URL.
        """
        if not image_path or not image_path.strip():
            return None

        clean_path = image_path.strip()
        if clean_path.startswith("http://") or clean_path.startswith("https://"):
            return clean_path

        try:
            settings = get_settings()
            base_url = settings.supabase_url.rstrip("/")
            # Normalize path: remove leading slash or 'words/' prefix if already in bucket
            rel_path = clean_path.lstrip("/")
            return f"{base_url}/storage/v1/object/public/{BUCKET_NAME}/{rel_path}"
        except (ConfigurationError, Exception) as e:
            logger.debug("Could not resolve Supabase storage URL: %s", e)
            return None

    @staticmethod
    def get_local_path(image_path: Optional[str]) -> Optional[Path]:
        """
        Check if a local image asset exists on disk in assets/images/words/.
        """
        if not image_path:
            return None

        filename = Path(image_path).name
        local_file = Path("assets/images/words") / filename
        if local_file.exists():
            return local_file
        return None

    @classmethod
    def display_word_image(
        cls,
        image_path: Optional[str],
        word_text: str,
        alt_text: str = "",
        theme_icon: str = "✨",
        accent_color: str = "#6366F1"
    ) -> None:
        """
        Safely render the word image with graceful fallback to local file or styled card.
        Never throws an exception or blanks the UI.
        """
        # 1. Attempt local file first (fastest and reliable in dev)
        local_file = cls.get_local_path(image_path)
        if local_file and local_file.exists():
            try:
                st.image(str(local_file), caption=alt_text or word_text.capitalize(), use_container_width=True)
                return
            except Exception as e:
                logger.warning("Failed to render local image %s: %s", local_file, e)

        # 2. Attempt remote Supabase Storage URL
        public_url = cls.get_public_url(image_path)
        if public_url:
            try:
                st.image(public_url, caption=alt_text or word_text.capitalize(), use_container_width=True)
                return
            except Exception as e:
                logger.warning("Failed to fetch remote image from %s: %s", public_url, e)

        # 3. Fallback placeholder card (rendered directly via st.html)
        safe_word = html.escape(word_text.upper())
        safe_accent = html.escape(accent_color)
        safe_icon = html.escape(theme_icon)

        card_html = (
            f'<div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%); '
            f'border: 2px dashed {safe_accent}; border-radius: 14px; padding: 2.5rem 1.5rem; text-align: center; margin-bottom: 1rem;">'
            f'<div style="font-size: 3rem; margin-bottom: 0.5rem;">{safe_icon}</div>'
            f'<div style="font-size: 1.4rem; font-weight: 700; color: #F8FAFC;">{safe_word}</div>'
            f'<div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.25rem;">Visual Vocabulary Card</div>'
            f'</div>'
        )

        st.html(card_html)


def get_image_service() -> ImageService:
    """Factory helper for ImageService."""
    return ImageService()
