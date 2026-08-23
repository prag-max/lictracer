@contextlib.contextmanager
def _tempfilepager(
    cmd_parts: list[str], color: bool | None = None
) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    """Page through text by invoking a program on a temporary file.

    Used as the primary pager strategy on Windows (where piping to
    ``more`` adds spurious ``\\r\\n``), and as a fallback on other
    platforms. The command is resolved to an absolute path with
    :func:`shutil.which`.
    """
    # Split the command into the invoked CLI and its parameters.
    if not cmd_parts:
        # No usable pager: fall back to stdout through _nullpager so it gets the
        # same borrowed-stream handling and the caller's stream is not closed.
        stdout = _default_text_stdout() or StringIO()
        with _nullpager(stdout, color) as rv:
            yield rv
        return

    import shutil
    import subprocess

    cmd = cmd_parts[0]

    cmd_filepath = shutil.which(cmd)
    if not cmd_filepath:
        # No usable pager: fall back to stdout through _nullpager so it gets the
        # same borrowed-stream handling and the caller's stream is not closed.
        stdout = _default_text_stdout() or StringIO()
        with _nullpager(stdout, color) as rv:
            yield rv
        return

    # Produces a normalized absolute path string.
    # multi-call binaries such as busybox derive their identity from the symlink
    # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    cmd_path = Path(cmd_filepath).absolute()

    import tempfile

    encoding = get_best_encoding(sys.stdout)
    if color is None:
        color = False
    # On Windows, NamedTemporaryFile cannot be opened by another process
    # while Python still has it open, so we use delete=False and clean up manually
    # rather than using a contextmanager here.
    f = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    try:
        yield t.cast(t.BinaryIO, f), encoding, color
        f.flush()
        f.close()
        subprocess.call([str(cmd_path), f.name])
    finally:
        os.unlink(f.name)