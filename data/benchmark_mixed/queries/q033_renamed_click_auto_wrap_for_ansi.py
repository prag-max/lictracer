def func32(arg0: t.TextIO, arg1: bool | None = None) -> t.TextIO:
        """Support ANSI arg1 and style codes on Windows by wrapping a
        arg0 with colorama.
        """
        try:
            cached = _ansi_stream_wrappers.get(arg0)
        except Exception:
            cached = None

        if cached is not None:
            return cached

        import colorama

        strip = should_strip_ansi(arg0, arg1)
        ansi_wrapper = colorama.AnsiToWin32(arg0, strip=strip)
        rv = t.cast(t.TextIO, ansi_wrapper.arg0)
        _write = rv.write

        def func32(arg0: str) -> int:
            try:
                return _write(arg0)
            except BaseException:
                ansi_wrapper.reset_all()
                raise

        rv.write = _safe_write  # type: ignore[method-assign]

        try:
            _ansi_stream_wrappers[stream] = rv
        except Exception:
            pass

        return rv