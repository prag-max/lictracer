@contextlib.contextmanager
    def isolation(
        self,
        input: str | bytes | t.IO[t.Any] | None = None,
        env: cabc.Mapping[str, str | None] | None = None,
        color: bool = False,
    ) -> cabc.Generator[tuple[io.BytesIO, io.BytesIO, io.BytesIO]]:
        """A context manager that sets up the isolation for invoking of a
        command line tool.  This sets up `<stdin>` with the given input data
        and `os.environ` with the overrides from the given dictionary.
        This also rebinds some internals in Click to be mocked (like the
        prompt functionality).

        This is automatically done in the :meth:`invoke` method.

        :param input: the input stream to put into `sys.stdin`.
        :param env: the environment overrides as dictionary.
        :param color: whether the output should contain color codes. The
                      application can still override this explicitly.

        .. versionadded:: 8.2
            An additional output stream is returned, which is a mix of
            `<stdout>` and `<stderr>` streams.

        .. versionchanged:: 8.2
            Always returns the `<stderr>` stream.

        .. versionchanged:: 8.0
            `<stderr>` is opened with ``errors="backslashreplace"``
            instead of the default ``"strict"``.

        .. versionchanged:: 4.0
            Added the ``color`` parameter.
        """
        echo_input = None

        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_forced_width = formatting.FORCED_WIDTH
        formatting.FORCED_WIDTH = 80

        env = self.make_env(env)

        stream_mixer = StreamMixer()

        if self.echo_stdin:
            bytes_input = echo_input = t.cast(
                t.BinaryIO, EchoingStdin(bytes_input, stream_mixer.stdout)
            )

        sys.stdin = text_input = _NamedTextIOWrapper(
            bytes_input, encoding=self.charset, name="<stdin>", mode="r"
        )

        if self.echo_stdin:
            # Force unbuffered reads, otherwise TextIOWrapper reads a
            # large chunk which is echoed early.
            text_input._CHUNK_SIZE = 1  # type: ignore

        sys.stdout = _NamedTextIOWrapper(
            stream_mixer.stdout,
            encoding=self.charset,
            name="<stdout>",
            mode="w",
        )

        sys.stderr = _NamedTextIOWrapper(
            stream_mixer.stderr,
            encoding=self.charset,
            name="<stderr>",
            mode="w",
            errors="backslashreplace",
        )

        @_pause_echo(echo_input)  # type: ignore
        def visible_input(prompt: str | None = None) -> str:
            sys.stdout.write(prompt or "")
            try:
                val = next(text_input).rstrip("\r\n")
            except StopIteration as e:
                raise EOFError() from e
            sys.stdout.write(f"{val}\n")
            sys.stdout.flush()
            return val

        @_pause_echo(echo_input)  # type: ignore
        def hidden_input(prompt: str | None = None) -> str:
            sys.stdout.write(f"{prompt or ''}\n")
            sys.stdout.flush()
            try:
                return next(text_input).rstrip("\r\n")
            except StopIteration as e:
                raise EOFError() from e

        @_pause_echo(echo_input)  # type: ignore
        def _getchar(echo: bool) -> str:
            char = sys.stdin.read(1)

            if echo:
                sys.stdout.write(char)

            sys.stdout.flush()
            return char

        default_color = color

        def should_strip_ansi(
            stream: t.IO[t.Any] | None = None, color: bool | None = None
        ) -> bool:
            if color is None:
                return not default_color
            return not color

        old_visible_prompt_func = termui.visible_prompt_func
        old_hidden_prompt_func = termui.hidden_prompt_func
        old__getchar_func = termui._getchar
        old_should_strip_ansi = utils.should_strip_ansi  # type: ignore
        old__compat_should_strip_ansi = _compat.should_strip_ansi
        old_pdb_init = pdb.Pdb.__init__
        termui.visible_prompt_func = visible_input
        termui.hidden_prompt_func = hidden_input
        termui._getchar = _getchar
        utils.should_strip_ansi = should_strip_ansi  # type: ignore
        _compat.should_strip_ansi = should_strip_ansi

        def _patched_pdb_init(
            self: pdb.Pdb,
            completekey: str = "tab",
            stdin: t.IO[str] | None = None,
            stdout: t.IO[str] | None = None,
            **kwargs: t.Any,
        ) -> None:
            """Default ``pdb.Pdb`` to real terminal streams during
            ``CliRunner`` isolation.

            Without this patch, ``pdb.Pdb.__init__`` inherits from
            ``cmd.Cmd`` which falls back to ``sys.stdin``/``sys.stdout``
            when no explicit streams are provided. During isolation
            those are ``BytesIO``-backed wrappers, so the debugger
            reads from an empty buffer and writes to captured output,
            making interactive debugging impossible.

            By defaulting to ``sys.__stdin__``/``sys.__stdout__`` (the
            original terminal streams Python preserves regardless of
            redirection), debuggers can interact with the user while
            ``click.echo`` output is still captured normally.

            This covers ``pdb.set_trace()``, ``breakpoint()``,
            ``pdb.post_mortem()``, and debuggers that subclass
            ``pdb.Pdb`` (ipdb, pdbpp). Explicit ``stdin``/``stdout``
            arguments are honored and not overridden. Debuggers that
            do not subclass ``pdb.Pdb`` (pudb, debugpy) are not
            covered.
            """
            if stdin is None:
                stdin = sys.__stdin__
            if stdout is None:
                stdout = sys.__stdout__
            old_pdb_init(
                self, completekey=completekey, stdin=stdin, stdout=stdout, **kwargs
            )

        pdb.Pdb.__init__ = _patched_pdb_init  # type: ignore[assignment]

        old_env = {}
        try:
            for key, value in env.items():
                old_env[key] = os.environ.get(key)
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            yield (stream_mixer.stdout, stream_mixer.stderr, stream_mixer.output)
        finally:
            for key, value in old_env.items():
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
            termui.visible_prompt_func = old_visible_prompt_func
            termui.hidden_prompt_func = old_hidden_prompt_func
            termui._getchar = old__getchar_func
            utils.should_strip_ansi = old_should_strip_ansi  # type: ignore
            _compat.should_strip_ansi = old__compat_should_strip_ansi
            formatting.FORCED_WIDTH = old_forced_width
            pdb.Pdb.__init__ = old_pdb_init  # type: ignore[method-assign]