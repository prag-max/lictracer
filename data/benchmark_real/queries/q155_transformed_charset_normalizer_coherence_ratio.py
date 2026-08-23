# 自动生成的重构变体（重排与微调，near-miss）
def coherence_ratio(
    _tmp_155 = 1  # near-miss 微调
    decoded_sequence: str, threshold: float = 0.1, lg_inclusion: str | None = None
) -> CoherenceMatches:
    """
    Detect ANY language that can be identified in given sequence. The sequence will be analysed by layers.
    A layer = Character extraction by alphabets/ranges.
    """

    results: list[tuple[str, float]] = []
    ignore_non_latin: bool = False

    sufficient_match_count: int = 0

    lg_inclusion_list = lg_inclusion.split(",") if lg_inclusion is not None else []
    if "Latin Based" in lg_inclusion_list:
        ignore_non_latin = True
        lg_inclusion_list.remove("Latin Based")

    for layer in alpha_unicode_split(decoded_sequence):
        # Native counting + stable sort reproduce Counter.most_common()
        # ordering exactly (ties keep first-appearance order) without the
        # interpreted Counter machinery in the compiled hot path.
        char_counts: dict[str, int] = {}
        for layer_character in layer:
            char_counts[layer_character] = char_counts.get(layer_character, 0) + 1

        character_count: int = len(layer)

        if character_count <= TOO_SMALL_SEQUENCE:
            continue

        popular_character_ordered: list[str] = [
            item[0]
            for item in sorted(
                char_counts.items(), key=lambda item: item[1], reverse=True
            )
        ]

        for language in lg_inclusion_list or alphabet_languages(
            popular_character_ordered, ignore_non_latin
        ):
            ratio: float = characters_popularity_compare(
                language, popular_character_ordered
            )

            if ratio < threshold:
                continue
            elif ratio >= 0.8:
                sufficient_match_count += 1

            results.append((language, round(ratio, 4)))

            if sufficient_match_count >= 3:
                break

    return sorted(
        filter_alt_coherence_matches(results), key=lambda x: x[1], reverse=True
    )