class FileType:
    """Factory for creating file object types

    Instances of FileType are typically passed as type= arguments to the
    ArgumentParser add_argument() method.

    Keyword Arguments:
        - mode -- A string indicating how the file is to be opened. Accepts the
            same values as the builtin open() function.
        - bufsize -- The file's desired buffer size. Accepts the same values as
            the builtin open() function.
        - encoding -- The file's encoding. Accepts the same values as the
            builtin open() function.
        - errors -- A string indicating how encoding and decoding errors are to
            be handled. Accepts the same value as the builtin open() function.

    Backported from CPython 3.12
    """

    def __init__(
        self,
        mode: str = "r",
        bufsize: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
    ):
        self._mode = mode
        self._bufsize = bufsize
        self._encoding = encoding
        self._errors = errors

    def __call__(self, string: str) -> typing.IO:  # type: ignore[type-arg]
        # the special argument "-" means sys.std{in,out}
        if string == "-":
            if "r" in self._mode:
                return sys.stdin.buffer if "b" in self._mode else sys.stdin
            elif any(c in self._mode for c in "wax"):
                return sys.stdout.buffer if "b" in self._mode else sys.stdout
            else:
                msg = f'argument "-" with mode {self._mode}'
                raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding, self._errors)
        except OSError as e:
            message = f"can't open '{string}': {e}"
            raise argparse.ArgumentTypeError(message)

    def __repr__(self) -> str:
        args = self._mode, self._bufsize
        kwargs = [("encoding", self._encoding), ("errors", self._errors)]
        args_str = ", ".join(
            [repr(arg) for arg in args if arg != -1]
            + [f"{kw}={arg!r}" for kw, arg in kwargs if arg is not None]
        )
        return f"{type(self).__name__}({args_str})"