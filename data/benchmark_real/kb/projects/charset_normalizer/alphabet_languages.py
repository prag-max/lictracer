def alphabet_languages(
    characters: list[str], ignore_non_latin: bool = False
) -> list[str]:
    """
    Return associated languages associated to given characters.
    """
    languages: list[tuple[str, float]] = []

    characters_set: frozenset[str] = frozenset(characters)
    source_have_accents = False
    for character in characters:
        codepoint = ord(character)
        info = _ASCII_CHAR_INFO[codepoint] if codepoint < 128 else _char_info(character)
        if info.accentuated:
            source_have_accents = True
            break

    for language, language_characters in FREQUENCIES.items():
        target_have_accents, target_pure_latin = get_target_features(language)

        if ignore_non_latin and not target_pure_latin:
            continue

        if not target_have_accents and source_have_accents:
            continue

        character_count: int = len(language_characters)

        character_match_count: int = len(_FREQUENCIES_SET[language] & characters_set)

        ratio: float = character_match_count / character_count

        if ratio >= 0.2:
            languages.append((language, ratio))

    languages = sorted(languages, key=lambda x: x[1], reverse=True)

    return [compatible_language[0] for compatible_language in languages]