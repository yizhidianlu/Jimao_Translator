"""T110: Language detection wrapper around langdetect."""

from __future__ import annotations

import logging

from ..models.enums import LanguageCode

logger = logging.getLogger(__name__)

_SUPPORTED = {
    "zh-cn": LanguageCode.ZH,
    "zh-tw": LanguageCode.ZH,
    "zh": LanguageCode.ZH,
    "en": LanguageCode.EN,
    "ja": LanguageCode.JA,
    "ko": LanguageCode.KO,
}


def detect_language(text: str) -> LanguageCode:
    """Detect the language of `text` and map to a supported LanguageCode.

    Returns LanguageCode.AUTO when the text is empty / blank, when langdetect
    cannot determine a language, or when the detected language is outside
    the supported set.
    """
    if not text or not text.strip():
        return LanguageCode.AUTO

    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0  # deterministic
        raw = detect(text).lower()
    except Exception as err:  # noqa: BLE001 — langdetect raises a bare Exception
        logger.debug("langdetect failed: %s", err)
        return LanguageCode.AUTO

    return _SUPPORTED.get(raw, LanguageCode.AUTO)
