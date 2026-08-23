def _character_flags(character: str) -> int:
    """Compute all name-based classification flags with a single unicodedata.name() call."""
    try:
        desc: str = unicodedata.name(character)
    except ValueError:
        return 0

    flags: int = 0

    if "LATIN" in desc:
        flags |= _LATIN
    if "CJK" in desc:
        flags |= _CJK
    if "HANGUL" in desc:
        flags |= _HANGUL
    if "KATAKANA" in desc:
        flags |= _KATAKANA
        if "HALFWIDTH" in desc:
            flags |= _HALFWIDTH_KATAKANA
    if "HIRAGANA" in desc:
        flags |= _HIRAGANA
    if "THAI" in desc:
        flags |= _THAI
    if "ARABIC" in desc:
        flags |= _ARABIC
        if "ISOLATED FORM" in desc:
            flags |= _ARABIC_ISOLATED_FORM
    if "LIGATURE" in desc or desc.endswith("LETTER AE"):
        flags |= _LIGATURE
    if "SUPERSCRIPT" in desc:
        flags |= _SUPERSCRIPT
    if desc in {"INVERTED QUESTION MARK", "INVERTED EXCLAMATION MARK"}:
        flags |= _SENTENCE_OPEN_PUNCTUATION

    for kw in _ACCENT_KEYWORDS:
        if kw in desc:
            flags |= _ACCENTUATED
            break

    return flags