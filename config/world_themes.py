"""World theme visual tokens and styling configuration for Pronunciation Adventure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class WorldTheme:
    key: str
    name: str
    icon: str
    badge_label: str
    accent_color: str          # Primary accent (e.g. #38BDF8)
    secondary_color: str       # Secondary accent (e.g. #0284C7)
    glow_color: str            # Neon glow / shadow (e.g. rgba(56, 189, 248, 0.4))
    card_bg_gradient: str      # Gradient for cards/panels
    banner_bg_gradient: str    # Hero / header gradient
    path_color: str            # Connection line / node color


DEFAULT_THEME = WorldTheme(
    key="default",
    name="Adventure Realm",
    icon="✨",
    badge_label="Pronunciation Realm",
    accent_color="#818CF8",
    secondary_color="#6366F1",
    glow_color="rgba(129, 140, 248, 0.4)",
    card_bg_gradient="linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%)",
    banner_bg_gradient="linear-gradient(135deg, rgba(79, 70, 229, 0.25) 0%, rgba(147, 51, 234, 0.25) 100%)",
    path_color="#6366F1"
)

WORLD_THEMES: Dict[str, WorldTheme] = {
    "village": WorldTheme(
        key="village",
        name="Sunlit Village",
        icon="🏡",
        badge_label="Village Path",
        accent_color="#38BDF8",
        secondary_color="#0284C7",
        glow_color="rgba(56, 189, 248, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(14, 165, 233, 0.2) 0%, rgba(30, 64, 175, 0.3) 100%)",
        path_color="#38BDF8"
    ),
    "forest": WorldTheme(
        key="forest",
        name="Whispering Forest",
        icon="🌲",
        badge_label="Forest Trail",
        accent_color="#4ADE80",
        secondary_color="#16A34A",
        glow_color="rgba(74, 222, 128, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(20, 83, 45, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(6, 78, 59, 0.35) 100%)",
        path_color="#4ADE80"
    ),
    "mountain": WorldTheme(
        key="mountain",
        name="Echo Mountain",
        icon="🏔️",
        badge_label="Mountain Ridge",
        accent_color="#F472B6",
        secondary_color="#DB2777",
        glow_color="rgba(244, 114, 182, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(131, 24, 67, 0.35) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(157, 23, 77, 0.35) 100%)",
        path_color="#F472B6"
    ),
    "ocean": WorldTheme(
        key="ocean",
        name="Coral Cove",
        icon="🌊",
        badge_label="Ocean Depths",
        accent_color="#2DD4BF",
        secondary_color="#0D9488",
        glow_color="rgba(45, 212, 191, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(19, 78, 74, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(20, 184, 166, 0.2) 0%, rgba(17, 94, 89, 0.35) 100%)",
        path_color="#2DD4BF"
    ),
    "desert": WorldTheme(
        key="desert",
        name="Golden Dunes",
        icon="🏜️",
        badge_label="Desert Oasis",
        accent_color="#FBBF24",
        secondary_color="#D97706",
        glow_color="rgba(251, 191, 36, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(120, 53, 15, 0.35) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(146, 64, 14, 0.35) 100%)",
        path_color="#FBBF24"
    ),
    "sky": WorldTheme(
        key="sky",
        name="Cloud Kingdom",
        icon="☁️",
        badge_label="Sky Peaks",
        accent_color="#C084FC",
        secondary_color="#9333EA",
        glow_color="rgba(192, 132, 252, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(88, 28, 135, 0.35) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(107, 33, 168, 0.35) 100%)",
        path_color="#C084FC"
    ),
    "crystal": WorldTheme(
        key="crystal",
        name="Crystal Caverns",
        icon="💎",
        badge_label="Crystal Mine",
        accent_color="#E879F9",
        secondary_color="#C026D3",
        glow_color="rgba(232, 121, 249, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(112, 26, 117, 0.35) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(217, 70, 239, 0.2) 0%, rgba(134, 25, 143, 0.35) 100%)",
        path_color="#E879F9"
    ),
    "castle": WorldTheme(
        key="castle",
        name="Royal Castle",
        icon="🏰",
        badge_label="Castle Keep",
        accent_color="#F59E0B",
        secondary_color="#D97706",
        glow_color="rgba(245, 158, 11, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(180, 83, 9, 0.35) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(146, 64, 14, 0.35) 100%)",
        path_color="#F59E0B"
    ),
    "space": WorldTheme(
        key="space",
        name="Space Station",
        icon="🚀",
        badge_label="Cosmic Orbit",
        accent_color="#6366F1",
        secondary_color="#4F46E5",
        glow_color="rgba(99, 102, 241, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(49, 46, 129, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(30, 27, 75, 0.4) 100%)",
        path_color="#6366F1"
    ),
    "galaxy": WorldTheme(
        key="galaxy",
        name="Starlight Galaxy",
        icon="🌌",
        badge_label="Deep Cosmos",
        accent_color="#A855F7",
        secondary_color="#9333EA",
        glow_color="rgba(168, 85, 247, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(88, 28, 135, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(59, 7, 100, 0.4) 100%)",
        path_color="#A855F7"
    ),
    "dragon": WorldTheme(
        key="dragon",
        name="Dragon Mountain",
        icon="🐉",
        badge_label="Dragon Peak",
        accent_color="#EF4444",
        secondary_color="#DC2626",
        glow_color="rgba(239, 68, 68, 0.4)",
        card_bg_gradient="linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(127, 29, 29, 0.4) 100%)",
        banner_bg_gradient="linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(69, 10, 10, 0.4) 100%)",
        path_color="#EF4444"
    )
}


def get_world_theme(theme_key: Optional[str]) -> WorldTheme:
    """Retrieve visual theme tokens for a given world theme key."""
    if not theme_key:
        return DEFAULT_THEME
    return WORLD_THEMES.get(theme_key.lower().strip(), DEFAULT_THEME)
