"""Tests validating brand design tokens, typography, and visual system invariants."""
from __future__ import annotations

import unittest
from config.design_tokens import (
    AUTHENTIC_TEAL,
    AUTHENTIC_TEAL_DARK,
    SIDECAR_YELLOW,
    SIDECAR_YELLOW_WARM,
    INK_GRAY,
    ANTIQUE_GOLD,
    TEXT_LIGHT_PRIMARY,
    TEXT_LIGHT_SECONDARY,
    TEXT_DARK_PRIMARY,
    TEXT_DARK_SECONDARY,
    TEXT_ON_DARK,
    MUTED_ON_DARK,
    TEXT_ON_LIGHT,
    MUTED_ON_LIGHT,
    get_global_css,
    calculate_contrast_ratio,
    calculate_relative_luminance,
    choose_contrast_color,
    get_foreground_for_background,
    hex_to_rgb,
)


class TestVisualDesignSystem(unittest.TestCase):
    """Test suite ensuring Authentic Teal, Sidecar Yellow, Ink Gray, Antique Gold, and General Sans compliance."""

    def test_brand_color_tokens(self):
        self.assertEqual(AUTHENTIC_TEAL.lower(), "#035352")
        self.assertEqual(SIDECAR_YELLOW.lower(), "#f3e8bc")
        self.assertEqual(INK_GRAY.lower(), "#2f3a3a")
        self.assertEqual(ANTIQUE_GOLD.lower(), "#c9a227")
        self.assertEqual(TEXT_LIGHT_PRIMARY.lower(), "#fffdf5")
        self.assertEqual(TEXT_LIGHT_SECONDARY.lower(), "#d8e3da")
        self.assertEqual(TEXT_DARK_PRIMARY.lower(), "#102a2a")
        self.assertEqual(TEXT_DARK_SECONDARY.lower(), "#365656")
        self.assertEqual(TEXT_ON_DARK.lower(), "#fffdf5")
        self.assertEqual(MUTED_ON_DARK.lower(), "#d8e3da")
        self.assertEqual(TEXT_ON_LIGHT.lower(), "#102a2a")
        self.assertEqual(MUTED_ON_LIGHT.lower(), "#365656")

    def test_global_css_contains_general_sans_and_brand_colors(self):
        css = get_global_css()
        self.assertIn("General Sans", css)
        self.assertIn("Inter", css)
        self.assertIn("#035352", css)
        self.assertIn("#F3E8BC", css)
        self.assertIn("#FFFDF5", css)
        self.assertIn("#102A2A", css)

    def test_wcag_contrast_engine(self):
        # Hex conversion
        self.assertEqual(hex_to_rgb("#035352"), (3, 83, 82))
        self.assertEqual(hex_to_rgb("F3E8BC"), (243, 232, 188))

        # Contrast calculation on Authentic Teal (#035352) -> Light Primary text (#FFFDF5)
        teal_light_ratio = calculate_contrast_ratio("#035352", "#FFFDF5")
        teal_dark_ratio = calculate_contrast_ratio("#035352", "#102A2A")
        self.assertGreater(teal_light_ratio, 8.0, "Light text on Authentic Teal must exceed WCAG AAA (7:1)")
        self.assertGreater(teal_light_ratio, teal_dark_ratio)

        # Contrast calculation on Sidecar Yellow (#F3E8BC) -> Dark Primary text (#102A2A)
        yellow_dark_ratio = calculate_contrast_ratio("#F3E8BC", "#102A2A")
        yellow_light_ratio = calculate_contrast_ratio("#F3E8BC", "#FFFDF5")
        self.assertGreater(yellow_dark_ratio, 10.0, "Dark text on Sidecar Yellow must exceed WCAG AAA (7:1)")
        self.assertGreater(yellow_dark_ratio, yellow_light_ratio)

        # Dynamic choice helper
        self.assertEqual(choose_contrast_color("#035352"), "#FFFDF5")
        self.assertEqual(choose_contrast_color("#023535"), "#FFFDF5")
        self.assertEqual(choose_contrast_color("#2F3A3A"), "#FFFDF5")
        self.assertEqual(choose_contrast_color("#F3E8BC"), "#102A2A")
        self.assertEqual(choose_contrast_color("#FFFDF5"), "#102A2A")
        self.assertEqual(choose_contrast_color("#FFFFFF"), "#102A2A")

        # Foreground helper
        self.assertEqual(get_foreground_for_background("#035352", is_secondary=False), "#FFFDF5")
        self.assertEqual(get_foreground_for_background("#035352", is_secondary=True), "#D8E3DA")
        self.assertEqual(get_foreground_for_background("#F3E8BC", is_secondary=False), "#102A2A")
        self.assertEqual(get_foreground_for_background("#F3E8BC", is_secondary=True), "#365656")
