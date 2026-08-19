"""Unit and integration tests for ImageService and Stage 10B Production Image Pipeline."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from services.image_service import ImageService, BUCKET_NAME


class TestImageServiceUnit:
    """Test unit behavior of ImageService URL resolution and fallbacks."""

    def test_get_public_url_relative_path(self):
        with patch("services.image_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(supabase_url="https://xyzcompany.supabase.co")
            url = ImageService.get_public_url("words/garden.webp")
            assert url == "https://xyzcompany.supabase.co/storage/v1/object/public/word-images/words/garden.webp"

    def test_get_public_url_absolute_http(self):
        url = ImageService.get_public_url("https://cdn.example.com/images/apple.png")
        assert url == "https://cdn.example.com/images/apple.png"

    def test_get_public_url_empty_or_none(self):
        assert ImageService.get_public_url("") is None
        assert ImageService.get_public_url(None) is None
        assert ImageService.get_public_url("   ") is None

    def test_get_local_path_existing_file(self):
        # We know acorn.webp or house.webp exists in assets/images/words
        path = ImageService.get_local_path("words/house.webp")
        assert path is not None
        assert path.exists()

    def test_get_local_path_nonexistent_file(self):
        path = ImageService.get_local_path("words/nonexistent_xyz_123.webp")
        assert path is None

    def test_display_word_image_local_hit(self):
        with patch("streamlit.image") as mock_img:
            ImageService.display_word_image(
                image_path="words/house.webp",
                word_text="house",
                alt_text="A cozy stone house",
            )
            mock_img.assert_called_once()
            assert "house.webp" in str(mock_img.call_args)

    def test_display_word_image_remote_fallback_when_no_local(self):
        with patch.object(ImageService, "get_local_path", return_value=None):
            with patch.object(ImageService, "get_public_url", return_value="https://cdn.example.com/pic.webp"):
                with patch("streamlit.image") as mock_img:
                    ImageService.display_word_image(
                        image_path="words/phantom.webp",
                        word_text="phantom",
                        alt_text="A gentle phantom",
                    )
                    mock_img.assert_called_once_with(
                        "https://cdn.example.com/pic.webp",
                        caption="A gentle phantom",
                        use_container_width=True
                    )

    def test_display_word_image_card_fallback_never_crashes(self):
        with patch.object(ImageService, "get_local_path", return_value=None):
            with patch.object(ImageService, "get_public_url", return_value=None):
                with patch("streamlit.html") as mock_html:
                    ImageService.display_word_image(
                        image_path=None,
                        word_text="mystery",
                        theme_icon="🔮",
                        accent_color="#8B5CF6"
                    )
                    mock_html.assert_called_once()
                    html_content = mock_html.call_args[0][0]
                    assert "MYSTERY" in html_content
                    assert "🔮" in html_content


class TestProductionImageCompleteness:
    """Verify that all 1,470 production words have valid image paths and alt text."""

    def test_all_production_words_have_images_and_alt_text(self):
        prod_path = Path("content/seed_words_prod.json")
        assert prod_path.exists(), "seed_words_prod.json must exist"

        with open(prod_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        words = data.get("words", [])
        assert len(words) == 1470, f"Expected 1470 words, got {len(words)}"

        missing_images = []
        missing_alt = []

        for w in words:
            img_path = w.get("image_path", "")
            alt_text = w.get("image_alt_text", "")

            if not img_path or not img_path.startswith("words/"):
                missing_images.append(w["text"])

            if not alt_text or len(alt_text.strip()) < 5:
                missing_alt.append(w["text"])

            # Verify local WebP asset exists on disk
            local_file = ImageService.get_local_path(img_path)
            assert local_file is not None and local_file.exists(), f"Missing local image for {w['text']}"
            assert local_file.stat().st_size < 50 * 1024, f"Image for {w['text']} exceeds 50KB limit"

        assert len(missing_images) == 0, f"Words missing valid image paths: {missing_images[:5]}"
        assert len(missing_alt) == 0, f"Words missing valid alt text: {missing_alt[:5]}"
