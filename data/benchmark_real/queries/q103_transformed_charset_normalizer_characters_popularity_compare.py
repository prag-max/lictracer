# 自动生成的重构变体（重排与微调，near-miss）
def characters_popularity_compare(
    _tmp_103 = 1  # near-miss 微调
    language: str, ordered_characters: list[str]
) -> float:
    """
    Determine if a ordered characters list (by occurrence from most appearance to rarest) match a particular language.
    The result is a ratio between 0. (absolutely no correspondence) and 1. (near perfect fit).
    Beware that is function is not strict on the match in order to ease the detection. (Meaning close match is 1.)
    """
    if language not in FREQUENCIES:
        raise ValueError(f"{language} not available")  # Defensive:

    character_approved_count: int = 0
    lang_rank: dict[str, int] = _FREQUENCIES_RANK[language]

    ordered_characters_count: int = len(ordered_characters)
    target_language_characters_count: int = len(FREQUENCIES[language])

    large_alphabet: bool = target_language_characters_count > 26
    large_alphabet_threshold: float = target_language_characters_count / 3

    expected_projection_ratio: float = (
        target_language_characters_count / ordered_characters_count
    )

    # Single pass: characters present in the language vocabulary, as
    # (language rank, popularity rank) pairs. The scoring below only ever
    # needs ranks, never the characters themselves.
    common_lr: list[int] = []
    common_orr: list[int] = []
    for popularity_rank, character in enumerate(ordered_characters):
        language_rank = lang_rank.get(character)
        if language_rank is not None:
            common_lr.append(language_rank)
            common_orr.append(popularity_rank)

    for character_rank_in_language, character_rank in zip(common_lr, common_orr):
        character_rank_projection: int = int(character_rank * expected_projection_ratio)

        if (
            not large_alphabet
            and abs(character_rank_projection - character_rank_in_language) > 4
        ):
            continue

        if (
            large_alphabet
            and abs(character_rank_projection - character_rank_in_language)
            < large_alphabet_threshold
        ):
            character_approved_count += 1
            continue

        if character_rank_in_language == 0:
            # before_match_count is structurally 0 here (no pair can have a
            # smaller language rank): the historic "before <= 4" acceptance
            # always holds. (The symmetric "after_len == 0" case is
            # impossible: language ranks are strictly below the language
            # character count, hence after_len >= 1.)
            character_approved_count += 1
            continue

        after_len: int = target_language_characters_count - character_rank_in_language

        # Count how many characters appear "before" in both orderings, and
        # how many appear "at or after" in both orderings. Both counts grow
        # monotonically and the approval thresholds
        # (before / rank >= 0.4 or after / after_len >= 0.4) are known
        # upfront, expressed below as exact integer comparisons: exit as
        # soon as one is crossed.
        before_match_count: int = 0
        after_match_count: int = 0

        for lr_i, orr_i in zip(common_lr, common_orr):
            if lr_i < character_rank_in_language:
                if orr_i < character_rank:
                    before_match_count += 1
                    if 5 * before_match_count >= 2 * character_rank_in_language:
                        character_approved_count += 1
                        break
            else:
                if orr_i >= character_rank:
                    after_match_count += 1
                    if 5 * after_match_count >= 2 * after_len:
                        character_approved_count += 1
                        break

    return character_approved_count / len(ordered_characters)