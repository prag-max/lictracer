def any_specified_encoding(
    sequence: bytes | bytearray, search_zone: int = 8192
) -> str | None:
    """
    Extract using ASCII-only decoder any specified encoding in the first n-bytes.
    """

    seq_len: int = len(sequence)

    # Cheap literal pre-filter.
    search_bytes = sequence[: min(seq_len, search_zone)]
    lowered_bytes = search_bytes.lower()
    if b"coding" not in lowered_bytes and b"charset" not in lowered_bytes:
        return None

    decoded_zone: str = search_bytes.decode("ascii", errors="ignore")

    for match in RE_POSSIBLE_ENCODING_INDICATION.finditer(decoded_zone):
        specified_encoding = match.group(1).lower().replace("-", "_")
        encoding_iana = _IANA_NAMES.get(specified_encoding)
        if encoding_iana is not None:
            return encoding_iana

    return None