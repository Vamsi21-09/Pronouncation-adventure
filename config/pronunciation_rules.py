"""Pronunciation rules and common mistake pattern guidance for English words."""
from __future__ import annotations

from typing import Optional

# Rule table mapping letter patterns / digraphs to friendly, child-focused explanations.
# Explicitly framed as spelling-pattern and articulation guidance, never claiming phoneme diagnosis.
PRONUNCIATION_RULES: dict[str, str] = {
    "th": "The 'th' sound is made by resting the tip of your tongue lightly between your upper and lower front teeth.",
    "ch": "The 'ch' sound begins with a quick, crisp burst (like in 'chair' or 'chest').",
    "sh": "The 'sh' sound is a smooth, quiet hush made by rounding your lips gently (like 'shhh').",
    "ph": "The letters 'ph' work together to create an 'f' sound (like in 'dolphin' or 'photo').",
    "wh": "Words with 'wh' start with soft rounded lips blowing gentle air (like 'whisper').",
    "wr": "In words starting with 'wr', the 'w' is silent, so start right on the 'r' sound (like 'write' or 'wrap').",
    "kn": "In words starting with 'kn', the 'k' is silent—begin speaking with the 'n' sound (like 'knight' or 'knee').",
    "gn": "In words starting with 'gn', the 'g' is silent (like 'gnome' or 'gnat').",
    "mb": "When words end with 'mb', the 'b' is silent (like in 'climb' or 'thumb').",
    "igh": "The 'igh' letter group teams up to make a long 'I' vowel sound (like in 'night' or 'light').",
    "tion": "The ending '-tion' is pronounced like 'shun' (like in 'action' or 'station').",
    "sion": "The ending '-sion' often makes a soft 'zhun' sound (like in 'vision').",
    "ea": "Vowel teams like 'ea' often stretch into a bright, long 'E' sound (like 'beach' or 'leaf').",
    "ee": "The double 'ee' stretches out into a long 'E' sound (like 'tree' or 'green').",
    "oa": "The 'oa' vowel team makes a long 'O' sound (like in 'boat' or 'oak').",
    "ow": "The 'ow' pattern sounds like 'O' (in 'snow') or 'ow' (in 'flower').",
    "oo": "The 'oo' sound is made by pushing your lips forward into a small circle (like in 'moon' or 'spoon').",
    "qu": "The 'qu' blend makes a quick 'kw' sound (like in 'quick' or 'queen').",
    "str": "The 'str' blend strings three sounds together smoothly: s-t-r (like in 'stream' or 'strong').",
    "spl": "The 'spl' blend combines s-p-l into one quick motion (like in 'splash').",
}


def lookup_pattern_rule(diff_text: str) -> Optional[str]:
    """
    Search the rule table for a matching phonetic or spelling pattern within the diff text.
    """
    clean = diff_text.lower().strip()
    if not clean:
        return None

    # Check direct match
    if clean in PRONUNCIATION_RULES:
        return PRONUNCIATION_RULES[clean]

    # Check substring containment (prioritizing longer patterns)
    for pattern, explanation in sorted(PRONUNCIATION_RULES.items(), key=lambda x: len(x[0]), reverse=True):
        if pattern in clean:
            return explanation

    return None
