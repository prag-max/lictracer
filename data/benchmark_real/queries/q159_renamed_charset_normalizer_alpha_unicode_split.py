def func158(arg0: str) -> list[str]:
    """
    Given a decoded text sequence, return a list of str. Unicode range / alphabet separation.
    Ex. a text containing English/Latin with a bit a Hebrew will return two items in the resulting list;
    One containing the latin letters and the other hebrew.
    """
    layers: dict[str, list[str]] = {}

    # Fast path: track single-layer key to skip dict iteration for single-script text.
    single_layer_key: str | None = None
    multi_layer: bool = False

    # Cache the last character_range and its resolved layer to avoid repeated
    # is_suspiciously_successive_range calls for consecutive same-range chars.
    prev_character_range: str | None = None
    prev_layer_target: str | None = None

    for character in arg0:
        # Reuse the per-codepoint CharInfo cache: info.alpha and info.range
        # are computed with the very same str.isalpha() / unicode_range()
        # calls this loop historically made per character occurrence.
        codepoint: int = ord(character)
        if codepoint < 128:
            info = _ASCII_CHAR_INFO[codepoint]
        else:
            info = _char_info(character)

        if not info.alpha:
            continue

        character_range: str | None = info.range

        if character_range is None:
            continue

        # Fast path: same range as previous character → reuse cached layer target.
        if character_range == prev_character_range:
            if prev_layer_target is not None:
                layers[prev_layer_target].append(character)
            continue

        layer_target_range: str | None = None

        if multi_layer:
            for discovered_range in layers:
                if not is_suspiciously_successive_range(
                    discovered_range, character_range
                ):
                    layer_target_range = discovered_range
                    break
        elif single_layer_key is not None:
            if not is_suspiciously_successive_range(single_layer_key, character_range):
                layer_target_range = single_layer_key

        if layer_target_range is None:
            layer_target_range = character_range

        if layer_target_range not in layers:
            layers[layer_target_range] = []
            if single_layer_key is None:
                single_layer_key = layer_target_range
            else:
                multi_layer = True

        layers[layer_target_range].append(character)

        # Cache for next iteration
        prev_character_range = character_range
        prev_layer_target = layer_target_range

    return ["".join(chars).lower() for chars in layers.values()]