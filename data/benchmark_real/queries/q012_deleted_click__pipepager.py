@contextlib.contextmanager
def _pipepager(
    cmd_parts: list[str], color: bool | None = None
) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    """Page through text by feeding it to another program.

    Invokes the pager via :class:`subprocess.Popen` with an ``argv`` list
    produced by :func:`shlex.split`. The command is resolved to an absolute
    path with :func:`shutil.which` as recommended by the
    :mod:`subprocess` docs for Windows compatibility.

    Invoking a pager through this might support colors: if piping to
    ``less`` and the user hasn't decided on colors, ``LESS=-R`` is set
    automatically.
    """
    # Split the command into the invoked CLI and its parameters.

    import shutil

    cmd = cmd_parts[0]
    cmd_params = cmd_parts[1:]

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
    cmd_name = cmd_path.name

    import subprocess

    # Make a local copy of the environment to not affect the global one.
    env = dict(os.environ)

    # If we're piping to less and the user hasn't decided on colors, we enable
    # them by default we find the -R flag in the command line arguments.
    if color is None and cmd_name == "less":
        less_flags = f"{os.environ.get('LESS', '')}{' '.join(cmd_params)}"
        if not less_flags:
            env["LESS"] = "-R"
            color = True
        elif "r" in less_flags or "R" in less_flags:
            color = True

    if color is None:
        color = False

    c = subprocess.Popen(
        [str(cmd_path)] + cmd_params,
        shell=False,
        stdin=subprocess.PIPE,
        env=env,
        errors="replace",
        text=True,
    )
    stdin = t.cast(t.BinaryIO, c.stdin)
    encoding = get_best_encoding(stdin)
    try:
        yield stdin, encoding, color
    except BrokenPipeError:
        # In case the pager exited unexpectedly, ignore the broken pipe error.
        pass
    except Exception as e:
        # In case there is an exception we want to close the pager immediately
        # and let the caller handle it.
        # Otherwise the pager will keep running, and the user may not notice
        # the error message, or worse yet it may leave the terminal in a broken state.
        c.terminate()
        raise e
    finally:
        # We must close stdin and wait for the pager to exit before we continue
        try:
            stdin.close()
        # Close implies flush, so it might throw a BrokenPipeError if the pager
        # process exited already.
        except BrokenPipeError:
            pass

        # Less doesn't respect ^C, but catches it for its own UI purposes (aborting
        # search or other commands inside less).
        #
        # That means when the user hits ^C, the parent process (click) terminates,
        # but less is still alive, paging the output and messing up the terminal.
        #
        # If the user wants to make the pager exit on ^C, they should set
        # `LESS='-K'`. It's not our decision to make.
        while True:
            try:
                c.wait()
            except KeyboardInterrupt:
                pass
            else:
                break