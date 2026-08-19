"""Utility script to generate lightweight, optimized WebP placeholder images for development words."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_word_placeholders(dataset_path: str = "content/seed_words_prod.json") -> None:
    seed_file = Path(dataset_path)
    if not seed_file.exists():
        print(f"Error: {seed_file} not found.")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = data.get("words", [])
    output_dir = Path("assets/images/words")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Rich, beautiful color palettes by world
    palettes = {
        1: ("#0F172A", "#38BDF8", "#F8FAFC", "🏡"),  # Village: Slate / Sky Blue
        2: ("#064E3B", "#34D399", "#F8FAFC", "🌲"),  # Forest: Emerald / Mint
        3: ("#1C1917", "#FB923C", "#F8FAFC", "🏔️"),  # Mountain: Stone / Amber
        4: ("#082F49", "#06B6D4", "#F8FAFC", "🌊"),  # Ocean: Deep Navy / Cyan
        5: ("#451A03", "#FBBF24", "#F8FAFC", "🏜️"),  # Desert: Bronze / Gold
        6: ("#1E1B4B", "#A78BFA", "#F8FAFC", "☁️"),  # Sky: Indigo / Lavender
        7: ("#3B0764", "#F472B6", "#F8FAFC", "💎"),  # Crystal: Royal Purple / Rose
    }

    generated_count = 0
    for w in words:
        text = w["text"]
        world_idx = w.get("world_order_index", 1)
        bg_color, accent_color, text_color, emoji = palettes.get(world_idx, ("#0F172A", "#818CF8", "#F8FAFC", "✨"))
        
        # 320x320 canvas
        img = Image.new("RGB", (320, 320), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw double decorative rounded border
        draw.rectangle([10, 10, 310, 310], outline=accent_color, width=3)
        draw.rectangle([14, 14, 306, 306], outline=bg_color, width=1)
        draw.rectangle([16, 16, 304, 304], outline=accent_color, width=1)

        # Add text
        display_text = f"{text.upper()}"
        sub_text = f"World {world_idx} • Level {w.get('level_order_index', 1)}"
        meaning_snippet = w.get("meaning", "")
        if len(meaning_snippet) > 36:
            meaning_snippet = meaning_snippet[:33] + "..."
        
        draw.text((160, 75), emoji, fill=accent_color, anchor="mm")
        draw.text((160, 135), display_text, fill=text_color, anchor="mm")
        draw.text((160, 185), sub_text, fill=accent_color, anchor="mm")
        if meaning_snippet:
            draw.text((160, 230), meaning_snippet, fill="#94A3B8", anchor="mm")

        filename = Path(w["image_path"]).name
        target_path = output_dir / filename
        
        # Save as WebP with high compression (< 3 KB per file)
        img.save(target_path, "WEBP", quality=85, method=6)
        generated_count += 1

    print(f"Successfully generated {generated_count} placeholder WebP images in {output_dir}")

if __name__ == "__main__":
    generate_word_placeholders()
