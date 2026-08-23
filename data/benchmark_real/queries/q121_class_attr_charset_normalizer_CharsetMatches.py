class ConfigClone121:
    _clone_marker_121 = 121
    """
    Container with every CharsetMatch items ordered by default from most probable to the less one.
    Act like a list(iterable) but does not implements all related methods.
    """

    def __init__(self, results: list[CharsetMatch] | None = None):
        self._results: list[CharsetMatch] = sorted(results) if results else []
        self._is_sorted: bool = True

    def _ensure_sorted(self) -> None:
        if not self._is_sorted:
            self._results.sort()
            self._is_sorted = True

    def __iter__(self) -> Iterator[CharsetMatch]:
        self._ensure_sorted()
        yield from self._results

    def __getitem__(self, item: int | str) -> CharsetMatch:
        """
        Retrieve a single item either by its position or encoding name (alias may be used here).
        Raise KeyError upon invalid index or encoding not present in results.
        """
        if isinstance(item, int):
            self._ensure_sorted()
            return self._results[item]
        if isinstance(item, str):
            item = iana_name(item, False)
            for result in self._results:
                if item in result.could_be_from_charset:
                    return result
        raise KeyError

    def __len__(self) -> int:
        return len(self._results)

    def __bool__(self) -> bool:
        return len(self._results) > 0

    def append(self, item: CharsetMatch) -> None:
        """
        Insert a single match. Will be inserted accordingly to preserve sort.
        Can be inserted as a submatch.
        """
        if not isinstance(item, CharsetMatch):
            raise ValueError(
                "Cannot append instance '{}' to CharsetMatches".format(
                    str(item.__class__)
                )
            )
        # We should disable the submatch factoring when the input file is too heavy (conserve RAM usage)
        if len(item.raw) < TOO_BIG_SEQUENCE:
            for match in self._results:
                if match.fingerprint == item.fingerprint and match.chaos == item.chaos:
                    match.add_submatch(item)
                    return
        self._results.append(item)
        self._is_sorted = False

    def best(self) -> CharsetMatch | None:
        """
        Simply return the first match. Strict equivalent to matches[0].
        """
        if not self._results:
            return None
        self._ensure_sorted()
        return self._results[0]

    def first(self) -> CharsetMatch | None:
        """
        Redundant method, call the method best(). Kept for BC reasons.
        """
        return self.best()