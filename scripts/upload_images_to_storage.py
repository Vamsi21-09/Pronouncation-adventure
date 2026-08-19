"""Developer utility script to upload pre-curated word images to Supabase Storage.

NOTE: This is an offline developer utility. It is NEVER called by the runtime Streamlit app.
Prerequisite: Ensure a public bucket named 'word-images' is created in your Supabase Dashboard
under Storage > Buckets.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Optional
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, ConfigurationError
from repositories.supabase_client import get_supabase_client

BUCKET_NAME = "word-images"
MAX_DIMENSION = 300  # Max width/height in px


def optimize_image_bytes(image_path: Path) -> bytes:
    """Resize (if exceeding max dimension) and return optimized WebP bytes."""
    with Image.open(image_path) as img:
        img_format = img.format
        width, height = img.size

        # Resize if larger than max dimensions while keeping aspect ratio
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        output_buffer = io.BytesIO()
        # Save as WebP
        img.save(output_buffer, format="WEBP", quality=80, method=6)
        return output_buffer.getvalue()


def upload_images(force: bool = False) -> None:
    """Upload all images from assets/images/words/ to Supabase Storage."""
    try:
        settings = get_settings()
        if not settings.is_configured():
            print("❌ Configuration Error: Supabase credentials not configured in secrets/env.")
            return
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        return

    client = get_supabase_client()
    images_dir = PROJECT_ROOT / "assets" / "images" / "words"

    if not images_dir.exists():
        print(f"❌ Images directory not found: {images_dir}")
        return

    image_files = sorted(list(images_dir.glob("*.webp")) + list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")))
    if not image_files:
        print(f"⚠️ No image files found in {images_dir}")
        return

    print(f"\n========================================================")
    print(f"  SUPABASE STORAGE UPLOADER - BUCKET: '{BUCKET_NAME}'")
    print(f"========================================================")
    print(f"Found {len(image_files)} local image(s) to process.\n")

    uploaded = 0
    skipped = 0
    failed = 0

    for img_file in image_files:
        storage_path = f"words/{img_file.name}"
        try:
            # Check if file already exists in bucket (unless force=True)
            if not force:
                try:
                    existing = client.storage.from_(BUCKET_NAME).list("words", {"search": img_file.name})
                    if existing and any(item.get("name") == img_file.name for item in existing):
                        print(f"  [SKIPPED] {storage_path} (Already exists in bucket)")
                        skipped += 1
                        continue
                except Exception:
                    pass  # Proceed to upload if list fails

            optimized_data = optimize_image_bytes(img_file)
            
            # Upload with upsert
            response = client.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=optimized_data,
                file_options={"content-type": "image/webp", "upsert": "true"}
            )
            print(f"  [UPLOADED] {storage_path} ({len(optimized_data)} bytes)")
            uploaded += 1
        except Exception as e:
            print(f"  [FAILED]   {storage_path} -> {e}")
            failed += 1

    print("\n--------------------------------------------------------")
    print(f"Upload Summary: {uploaded} Uploaded | {skipped} Skipped | {failed} Failed")
    print("--------------------------------------------------------\n")


if __name__ == "__main__":
    force_upload = "--force" in sys.argv
    upload_images(force=force_upload)
