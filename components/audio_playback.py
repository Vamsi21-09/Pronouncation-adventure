"""Audio playback component for target vocabulary pronunciation in Pronunciation Adventure."""
from __future__ import annotations

import html
import json
import streamlit as st
import streamlit.components.v1 as components


def get_hear_word_button_html(word_text: str, button_id: str = "hear_word_btn") -> str:
    """
    Returns the standalone HTML/JS document for the 'Hear Word' audio button.
    Supports SpeechSynthesis with automatic HTML5 Audio fallback for guaranteed audio delivery.
    """
    safe_word = html.escape(word_text.strip())
    js_word = json.dumps(word_text.strip())
    sanitized_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in button_id)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @import url('https://api.fontshare.com/v2/css?f[]=general-sans@600,700,800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600&display=swap');

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'General Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        body {{
            background: transparent;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            overflow: hidden;
            width: 100%;
            height: 100%;
            padding: 2px;
        }}

        .hear-btn-wrapper {{
            display: inline-flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 4px;
        }}

        .hear-word-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #FFFDF5;
            color: #102A2A;
            border: 1.5px solid rgba(47, 58, 58, 0.35);
            border-radius: 12px;
            padding: 8px 16px;
            font-size: 0.94rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(47, 58, 58, 0.08);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
            outline: none;
            white-space: nowrap;
        }}

        .hear-word-btn:hover {{
            background: #F3E8BC;
            border-color: #035352;
            color: #035352;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(3, 83, 82, 0.15);
        }}

        .hear-word-btn:active {{
            transform: translateY(0);
        }}

        .hear-word-btn.is-playing {{
            background: #FAF5DC;
            border-color: #C9A227;
            color: #102A2A;
            box-shadow: 0 0 12px rgba(201, 162, 39, 0.4);
            animation: hearPulse 1.2s infinite ease-in-out;
        }}

        @keyframes hearPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.03); }}
        }}

        .hear-word-error {{
            color: #C2410C;
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem;
            font-weight: 600;
            display: none;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="hear-btn-wrapper">
        <button
            id="{sanitized_id}"
            type="button"
            class="hear-word-btn"
            title="Listen to correct pronunciation of {safe_word}"
            aria-label="Listen to pronunciation of {safe_word}"
        >
            🔊 Hear Word
        </button>
        <div id="{sanitized_id}_err" class="hear-word-error">
            Audio playback isn’t available. Please try again.
        </div>
    </div>

    <script>
        (function() {{
            var word = {js_word};
            var btn = document.getElementById('{sanitized_id}');
            var errEl = document.getElementById('{sanitized_id}_err');
            var currentAudio = null;

            function showError() {{
                if (errEl) errEl.style.display = 'block';
            }}

            function hideError() {{
                if (errEl) errEl.style.display = 'none';
            }}

            function setPlaying(playing) {{
                if (!btn) return;
                if (playing) {{
                    btn.innerHTML = '🔊 Playing...';
                    btn.classList.add('is-playing');
                }} else {{
                    btn.innerHTML = '🔊 Hear Again';
                    btn.classList.remove('is-playing');
                }}
            }}

            // Pre-load speech synthesis voices
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.getVoices();
                if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                    window.speechSynthesis.onvoiceschanged = function() {{
                        window.speechSynthesis.getVoices();
                    }};
                }}
            }}

            function playAudioFallback() {{
                try {{
                    if (currentAudio) {{
                        currentAudio.pause();
                        currentAudio = null;
                    }}
                    // Open-standard English dictionary TTS pronunciation stream
                    var audioUrl = 'https://dict.youdao.com/dictvoice?audio=' + encodeURIComponent(word) + '&type=2';
                    currentAudio = new Audio(audioUrl);
                    
                    setPlaying(true);
                    hideError();

                    currentAudio.onended = function() {{
                        setPlaying(false);
                    }};

                    currentAudio.onerror = function() {{
                        // Secondary fallback: Google TTS stream
                        try {{
                            var gUrl = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q=' + encodeURIComponent(word);
                            currentAudio = new Audio(gUrl);
                            currentAudio.onended = function() {{ setPlaying(false); }};
                            currentAudio.onerror = function() {{
                                setPlaying(false);
                                showError();
                            }};
                            currentAudio.play().catch(function() {{
                                setPlaying(false);
                                showError();
                            }});
                        }} catch(e) {{
                            setPlaying(false);
                            showError();
                        }}
                    }};

                    currentAudio.play().catch(function() {{
                        setPlaying(false);
                        showError();
                    }});
                }} catch(err) {{
                    setPlaying(false);
                    showError();
                }}
            }}

            function playSpeech() {{
                hideError();

                if (!('speechSynthesis' in window)) {{
                    playAudioFallback();
                    return;
                }}

                try {{
                    window.speechSynthesis.cancel();
                    window.speechSynthesis.resume();

                    var utterance = new SpeechSynthesisUtterance(word);
                    utterance.lang = 'en-US';
                    utterance.rate = 0.85;
                    utterance.pitch = 1.0;

                    var voices = window.speechSynthesis.getVoices();
                    if (voices && voices.length > 0) {{
                        var enVoice = voices.find(function(v) {{
                            return v.lang && (v.lang === 'en-US' || v.lang.startsWith('en'));
                        }});
                        if (enVoice) {{
                            utterance.voice = enVoice;
                        }}
                    }}

                    var started = false;
                    utterance.onstart = function() {{
                        started = true;
                        setPlaying(true);
                    }};

                    utterance.onend = function() {{
                        setPlaying(false);
                    }};

                    utterance.onerror = function(e) {{
                        console.warn('SpeechSynthesis error, using fallback:', e);
                        playAudioFallback();
                    }};

                    window.speechSynthesis.speak(utterance);

                    // If speech synthesis doesn't trigger onstart within 600ms (common Chromium bug), use Audio fallback
                    setTimeout(function() {{
                        if (!started && (!window.speechSynthesis.speaking && !window.speechSynthesis.pending)) {{
                            console.log('SpeechSynthesis idle timeout, falling back to Audio stream.');
                            playAudioFallback();
                        }}
                    }}, 600);

                }} catch(e) {{
                    console.warn('SpeechSynthesis exception, fallback to audio stream:', e);
                    playAudioFallback();
                }}
            }}

            if (btn) {{
                btn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    playSpeech();
                }});
            }}
        }})();
    </script>
</body>
</html>"""


def render_hear_word_button(word_text: str, key: str = "hear_word_btn") -> None:
    """
    Renders the lightweight, client-side 'Hear Word' button in Streamlit via components.html.
    Guarantees active JavaScript execution, event listeners, and dual-engine audio playback.
    """
    html_content = get_hear_word_button_html(word_text, button_id=key)
    components.html(html_content, height=48, scrolling=False)
