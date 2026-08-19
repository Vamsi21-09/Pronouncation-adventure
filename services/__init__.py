"""Services module for Pronunciation Adventure."""
from .auth_service import AuthService, AuthResult, get_auth_service
from .progression_service import ProgressionService, get_progression_service
from .override_service import OverrideService, get_override_service
from .image_service import ImageService, get_image_service
from .speech_service import (
    SpeechService,
    TranscriptResult,
    get_speech_service,
    ERROR_PERMISSION_DENIED,
    ERROR_NO_SPEECH,
    ERROR_AUDIO_TIMEOUT,
    ERROR_UNSUPPORTED_BROWSER,
    ERROR_NETWORK,
    ERROR_API_FAILURE,
    PROVIDER_WEB_SPEECH,
    PROVIDER_SERVER_FALLBACK,
)
from .scoring_service import (
    ScoringService,
    ScoreResult,
    DiffSegment,
    get_scoring_service,
    normalize,
    align_words,
)

__all__ = [
    "AuthService",
    "AuthResult",
    "get_auth_service",
    "ProgressionService",
    "get_progression_service",
    "OverrideService",
    "get_override_service",
    "ImageService",
    "get_image_service",
    "SpeechService",
    "TranscriptResult",
    "get_speech_service",
    "ERROR_PERMISSION_DENIED",
    "ERROR_NO_SPEECH",
    "ERROR_AUDIO_TIMEOUT",
    "ERROR_UNSUPPORTED_BROWSER",
    "ERROR_NETWORK",
    "ERROR_API_FAILURE",
    "PROVIDER_WEB_SPEECH",
    "PROVIDER_SERVER_FALLBACK",
    "ScoringService",
    "ScoreResult",
    "DiffSegment",
    "get_scoring_service",
    "normalize",
    "align_words",
]
