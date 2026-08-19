"""Pronunciation Adventure - Brand Visual Design Tokens and Shared Styling."""
from __future__ import annotations

# ==========================================
# 1. CORE TWO-COLOR BRAND TOKENS
# ==========================================
# Dominant Light Surface (~70%)
SIDECAR_YELLOW = "#F3E8BC"
SIDECAR_YELLOW_LIGHT = "#FAF5DC"
SIDECAR_YELLOW_WARM = "#EBDD9F"
SIDECAR_YELLOW_SURFACE = "#FFFDF5"
SIDECAR_YELLOW_BORDER = "rgba(47, 58, 58, 0.35)"

# Primary Brand & Structural Frame (~30%)
AUTHENTIC_TEAL = "#035352"
AUTHENTIC_TEAL_DARK = "#023535"
AUTHENTIC_TEAL_DEEP = "#012424"
AUTHENTIC_TEAL_SURFACE = "#044443"
AUTHENTIC_TEAL_LIGHT = "#0A6E6D"
AUTHENTIC_TEAL_BORDER = "rgba(243, 232, 188, 0.3)"

# Neutral Outlines & Separators Only
INK_GRAY = "#2F3A3A"
INK_GRAY_LIGHT = "#3D4B4B"
INK_GRAY_BORDER = "rgba(47, 58, 58, 0.35)"

# Special Rewards & Accents Only
ANTIQUE_GOLD = "#C9A227"
ANTIQUE_GOLD_LIGHT = "#DFC053"
ANTIQUE_GOLD_BORDER = "rgba(201, 162, 39, 0.4)"

# ==========================================
# 2. STRICT CONTRAST-CHECKED TEXT TOKENS
# ==========================================
TEXT_LIGHT_PRIMARY = "#FFFDF5"     # High contrast on Authentic Teal (#035352) & Ink Gray (#2F3A3A)
TEXT_LIGHT_SECONDARY = "#D8E3DA"   # Soft mint-sage on Authentic Teal (#035352)
TEXT_DARK_PRIMARY = "#102A2A"      # High contrast on Sidecar Yellow (#F3E8BC) & Light surfaces
TEXT_DARK_SECONDARY = "#365656"    # Medium dark slate on Sidecar Yellow (#F3E8BC) & Light surfaces

# Semantic Aliases
TEXT_ON_DARK = TEXT_LIGHT_PRIMARY       # #FFFDF5
MUTED_ON_DARK = TEXT_LIGHT_SECONDARY    # #D8E3DA
TEXT_ON_LIGHT = TEXT_DARK_PRIMARY       # #102A2A
MUTED_ON_LIGHT = TEXT_DARK_SECONDARY    # #365656

# ==========================================
# 3. ACCENT & SEMANTIC TOKENS
# ==========================================
GOLD_STAR = "#C9A227"
SUCCESS_EMERALD = "#10B981"
DANGER_CORAL = "#EF4444"
INFO_SKY = "#38BDF8"


# ==========================================
# 4. CENTRAL WCAG CONTRAST ENGINE
# ==========================================
def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. '#035352' or '035352') to (R, G, B) tuple."""
    hex_clean = hex_code.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    elif len(hex_clean) != 6:
        return (0, 0, 0)
    return (int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16))


def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1 specification."""
    def _srgb_to_linear(c: int) -> float:
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4

    r_lin = _srgb_to_linear(r)
    g_lin = _srgb_to_linear(g)
    b_lin = _srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calculate_contrast_ratio(color1_hex: str, color2_hex: str) -> float:
    """Calculate the WCAG contrast ratio between two hex colors (1.0 to 21.0)."""
    r1, g1, b1 = hex_to_rgb(color1_hex)
    r2, g2, b2 = hex_to_rgb(color2_hex)
    lum1 = calculate_relative_luminance(r1, g1, b1)
    lum2 = calculate_relative_luminance(r2, g2, b2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def choose_contrast_color(
    background_color: str,
    candidates: list[str] | None = None,
    preferred_light: str = TEXT_LIGHT_PRIMARY,
    preferred_dark: str = TEXT_DARK_PRIMARY,
) -> str:
    """Select the candidate foreground color providing the strongest contrast against background_color."""
    if not candidates:
        candidates = [preferred_light, preferred_dark]

    best_candidate = candidates[0]
    best_ratio = -1.0
    for cand in candidates:
        ratio = calculate_contrast_ratio(background_color, cand)
        if ratio > best_ratio:
            best_ratio = ratio
            best_candidate = cand

    return best_candidate


def get_foreground_for_background(
    background_color: str,
    is_secondary: bool = False,
) -> str:
    """Returns the optimal foreground text color (primary or muted) for a given background color."""
    light_fg = TEXT_LIGHT_SECONDARY if is_secondary else TEXT_LIGHT_PRIMARY
    dark_fg = TEXT_DARK_SECONDARY if is_secondary else TEXT_DARK_PRIMARY
    return choose_contrast_color(
        background_color,
        candidates=[light_fg, dark_fg],
        preferred_light=light_fg,
        preferred_dark=dark_fg,
    )


def get_global_css() -> str:
    """Returns the shared core CSS containing General Sans typography, contrast tokens, and base styling."""
    return f"""
    <style>
        /* General Sans & Inter Fonts */
        @import url('https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700,800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        /* Global Typography Defaults */
        html, body, [class*="css"], .stMarkdown, .stText {{
            font-family: 'General Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            color: {TEXT_DARK_PRIMARY};
        }}

        /* Headings Hierarchy */
        h1, h2, h3, h4, h5, h6, .game-title, .brand-title {{
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            color: {TEXT_DARK_PRIMARY};
            letter-spacing: -0.01em;
        }}

        h1 {{ font-weight: 800 !important; }}

        /* Paragraphs & Long-form text on Light Canvas */
        p, .readable-text, .word-meaning, .word-example, .helper-text {{
            font-family: 'Inter', sans-serif !important;
            line-height: 1.6;
            color: {TEXT_DARK_SECONDARY};
        }}

        /* Captions & Subtitles on Light Surface */
        .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
            color: {TEXT_DARK_SECONDARY} !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
        }}

        /* Labels across all Streamlit widgets on light surfaces */
        label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {{
            color: {TEXT_DARK_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
        }}

        /* App Background: 70% Warm Sidecar Yellow / Cream Surface */
        .stApp {{
            background: linear-gradient(180deg, #FBF8EA 0%, {SIDECAR_YELLOW} 100%) !important;
            color: {TEXT_DARK_PRIMARY} !important;
        }}

        /* Main Content Container Spacing */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1080px !important;
        }}

        /* All Streamlit Button & Popover Containers: Pure transparent single-layer wrapper */
        div.stButton,
        div[data-testid="stButton"],
        div[data-testid="stPopover"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        /* Streamlit Primary Buttons: Authentic Teal with Light Cream text */
        button[kind="primary"],
        .stButton > button[kind="primary"],
        div.stButton > button[type="primary"],
        [data-testid="stBaseButton-primary"] {{
            background: {AUTHENTIC_TEAL} !important;
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            border: 1.5px solid {INK_GRAY} !important;
            border-radius: 14px !important;
            box-shadow: 0 4px 14px rgba(3, 83, 82, 0.25) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            outline: none !important;
        }}

        button[kind="primary"]:hover,
        div.stButton > button[type="primary"]:hover,
        [data-testid="stBaseButton-primary"]:hover {{
            background: {AUTHENTIC_TEAL_LIGHT} !important;
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
            border-color: {AUTHENTIC_TEAL} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(3, 83, 82, 0.35) !important;
        }}

        /* Streamlit Secondary Buttons: Warm Cream / White Surface with Ink Gray border */
        button[kind="secondary"],
        .stButton > button:not([kind="primary"]):not([type="primary"]),
        div.stButton > button:not([kind="primary"]):not([type="primary"]),
        [data-testid="stBaseButton-secondary"] {{
            background: #FFFDF5 !important;
            color: {TEXT_DARK_PRIMARY} !important;
            fill: {TEXT_DARK_PRIMARY} !important;
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            border: 1.5px solid {INK_GRAY_BORDER} !important;
            border-radius: 14px !important;
            box-shadow: 0 2px 8px rgba(47, 58, 58, 0.08) !important;
            transition: all 0.2s ease !important;
            outline: none !important;
        }}

        button[kind="secondary"]:hover,
        div.stButton > button:not([kind="primary"]):not([type="primary"]):hover,
        [data-testid="stBaseButton-secondary"]:hover {{
            background: {SIDECAR_YELLOW_LIGHT} !important;
            border-color: {AUTHENTIC_TEAL} !important;
            color: {AUTHENTIC_TEAL} !important;
            fill: {AUTHENTIC_TEAL} !important;
            transform: translateY(-1px) !important;
        }}

        /* Strip ALL inner backgrounds, borders, shadows, and outlines from child text wrappers */
        button[kind="primary"] *,
        button[kind="secondary"] *,
        .stButton > button *,
        div.stButton > button *,
        [data-testid="stPopover"] > button * {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        /* Inherit correct contrast colors inside children */
        button[kind="primary"] *,
        .stButton > button[kind="primary"] *,
        div.stButton > button[type="primary"] * {{
            color: {TEXT_LIGHT_PRIMARY} !important;
            fill: {TEXT_LIGHT_PRIMARY} !important;
        }}

        button[kind="secondary"] *,
        .stButton > button:not([kind="primary"]):not([type="primary"]) *,
        div.stButton > button:not([kind="primary"]):not([type="primary"]) * {{
            color: {TEXT_DARK_PRIMARY} !important;
            fill: {TEXT_DARK_PRIMARY} !important;
        }}

        /* Disabled Buttons */
        button:disabled,
        div.stButton > button:disabled {{
            opacity: 0.65 !important;
            cursor: not-allowed !important;
            transform: none !important;
            background: rgba(47, 58, 58, 0.1) !important;
            border-color: rgba(47, 58, 58, 0.25) !important;
            color: {TEXT_DARK_SECONDARY} !important;
            fill: {TEXT_DARK_SECONDARY} !important;
        }}

        button:disabled *,
        div.stButton > button:disabled * {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: {TEXT_DARK_SECONDARY} !important;
            fill: {TEXT_DARK_SECONDARY} !important;
        }}

        /* Hear Word Pronunciation Button (Secondary Audio Control) */
        .hear-word-btn {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 6px !important;
            background: #FFFDF5 !important;
            color: #102A2A !important;
            border: 1.5px solid rgba(47, 58, 58, 0.35) !important;
            border-radius: 12px !important;
            padding: 7px 15px !important;
            font-family: 'General Sans', sans-serif !important;
            font-size: 0.92rem !important;
            font-weight: 700 !important;
            cursor: pointer !important;
            box-shadow: 0 2px 6px rgba(47, 58, 58, 0.08) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            user-select: none !important;
            text-decoration: none !important;
            outline: none !important;
        }}

        .hear-word-btn:hover {{
            background: #F3E8BC !important;
            border-color: #035352 !important;
            color: #035352 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(3, 83, 82, 0.15) !important;
        }}

        .hear-word-btn:active {{
            transform: translateY(0) !important;
        }}

        .hear-word-btn.is-playing {{
            background: #FAF5DC !important;
            border-color: #C9A227 !important;
            color: #102A2A !important;
            box-shadow: 0 0 12px rgba(201, 162, 39, 0.4) !important;
            animation: hearWordPulse 1.2s infinite ease-in-out !important;
        }}

        @keyframes hearWordPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.03); }}
        }}

        .hear-word-error {{
            color: #C2410C !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            margin-top: 5px !important;
        }}

        /* Streamlit Inputs & Selectors */
        .stTextInput > div > div > input, .stSelectbox > div > div > div {{
            background: #FFFDF5 !important;
            color: {TEXT_DARK_PRIMARY} !important;
            border: 1.5px solid {INK_GRAY_BORDER} !important;
            border-radius: 12px !important;
            font-family: 'General Sans', sans-serif !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: {TEXT_DARK_SECONDARY} !important;
            opacity: 0.8 !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {AUTHENTIC_TEAL} !important;
            box-shadow: 0 0 0 2px rgba(3, 83, 82, 0.2) !important;
        }}

        /* Streamlit Tabs on Light Surface */
        button[data-baseweb="tab"], button[data-baseweb="tab"] * {{
            font-family: 'General Sans', sans-serif !important;
            font-weight: 700 !important;
            color: {TEXT_DARK_SECONDARY} !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"],
        button[data-baseweb="tab"][aria-selected="true"] * {{
            color: {AUTHENTIC_TEAL} !important;
            border-bottom-color: {AUTHENTIC_TEAL} !important;
        }}

        /* Streamlit Popover & Forms */
        [data-testid="stPopoverBody"] {{
            background: #FFFDF5 !important;
            border: 1.5px solid {INK_GRAY} !important;
            border-radius: 16px !important;
            box-shadow: 0 12px 36px rgba(47, 58, 58, 0.25) !important;
            color: {TEXT_DARK_PRIMARY} !important;
        }}

        /* Glassmorphism Dark Authentic Teal Structural Card */
        .card-teal, .dashboard-teal-card, .home-hero-card, .mic-header {{
            background: linear-gradient(135deg, {AUTHENTIC_TEAL} 0%, {AUTHENTIC_TEAL_DARK} 100%);
            border: 1.5px solid rgba(243, 232, 188, 0.3);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 8px 24px rgba(3, 83, 82, 0.3);
            color: {TEXT_LIGHT_PRIMARY};
        }}

        .card-teal h1, .card-teal h2, .card-teal h3, .card-teal h4, .card-teal strong,
        .dashboard-teal-card h1, .dashboard-teal-card h2, .dashboard-teal-card h3, .dashboard-teal-card h4, .dashboard-teal-card strong,
        .home-hero-card h1, .home-hero-card h2, .home-hero-card h3, .home-hero-card h4, .home-hero-card strong,
        .mic-header h1, .mic-header h2, .mic-header h3, .mic-header h4, .mic-header strong {{
            color: {TEXT_LIGHT_PRIMARY} !important;
        }}

        .card-teal p, .card-teal .sub,
        .dashboard-teal-card p, .dashboard-teal-card .sub,
        .home-hero-card p, .home-hero-card .sub,
        .mic-header p, .mic-header .sub {{
            color: {TEXT_LIGHT_SECONDARY} !important;
        }}

        /* Sidecar Yellow / Warm Cream Light Surface Card (Dominant ~70%) */
        .card-yellow, .card-cream, .card-info, .card-surface, .frontier-card, .stat-box, .target-word-card, .meaning-box, .info-card {{
            background: #FFFDF5;
            border: 1.5px solid {INK_GRAY_BORDER};
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 6px 20px rgba(47, 58, 58, 0.08);
            color: {TEXT_DARK_PRIMARY};
        }}

        .card-yellow h1, .card-yellow h2, .card-yellow h3, .card-yellow h4, .card-yellow strong,
        .card-cream h1, .card-cream h2, .card-cream h3, .card-cream h4, .card-cream strong,
        .card-info h1, .card-info h2, .card-info h3, .card-info h4, .card-info strong,
        .card-surface h1, .card-surface h2, .card-surface h3, .card-surface h4, .card-surface strong,
        .frontier-card h1, .frontier-card h2, .frontier-card h3, .frontier-card h4, .frontier-card strong,
        .target-word-card h1, .target-word-card h2, .target-word-card h3, .target-word-card strong {{
            color: {TEXT_DARK_PRIMARY} !important;
        }}

        .card-yellow p, .card-yellow .caption, .card-yellow .sub,
        .card-cream p, .card-cream .caption, .card-cream .sub,
        .card-info p, .card-info .caption, .card-info .sub,
        .card-surface p, .card-surface .caption, .card-surface .sub,
        .frontier-card p, .info-card p, .info-card li {{
            color: {TEXT_DARK_SECONDARY} !important;
        }}

        /* Subtle status badge */
        .badge-brand {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(3, 83, 82, 0.12);
            color: {AUTHENTIC_TEAL};
            border: 1px solid rgba(3, 83, 82, 0.25);
        }}
    </style>
    """
