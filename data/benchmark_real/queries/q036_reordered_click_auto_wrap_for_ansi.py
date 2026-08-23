def auto_wrap_for_ansi(stream: t.TextIO, color: bool | None = None) -> t.TextIO:
        """Support ANSI color and style codes on Windows by wrapping a
        stream with colorama.
        """
        try:
            cached = _ansi_stream_wrappers.get(stream)
        except Exception:
            cached = None

        if cached is not None:
            return cached

        strip = should_strip_ansi(stream, color)
        import colorama
        ansi_wrapper = colorama.AnsiToWin32(stream, strip=strip)
        rv = t.cast(t.TextIO, ansi_wrapper.stream)
        _write = rv.write

        def _safe_write(s: str) -> int:
            try:
                return _write(s)
            except BaseException:
                ansi_wrapper.reset_all()
                raise

        rv.write = _safe_write  # type: ignore[method-assign]

        try:
            _ansi_stream_wrappers[stream] = rv
        except Exception:
            pass

        return rv