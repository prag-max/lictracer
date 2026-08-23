def find_and_update_from_json(*dirs, **kwargs):
    """Find a mozinfo.json file, load it, and update global symbol table.

    This method will first check the relevant objdir directory for the
    necessary mozinfo.json file, if the current script is being run from a
    Mozilla objdir.

    If the objdir directory did not supply the necessary data, this method
    will then look for the required mozinfo.json file from the provided
    tuple of directories.

    If file is found, the global symbols table is updated via a helper method.

    If no valid files are found, this method no-ops unless the raise_exception
    kwargs is provided with explicit boolean value of True.

    :param tuple dirs: Directories in which to look for the file.
    :param dict kwargs: optional values:
                        raise_exception: if True, exceptions are raised.
                        False by default.
    :returns: None: default behavior if mozinfo.json cannot be found.
              json_path: string representation of mozinfo.json path.
    :raises: IOError: if raise_exception is True and file is not found.
    """
    # First, see if we're in an objdir
    try:
        from mozboot.mozconfig import MozconfigFindException
        from mozbuild.base import BuildEnvironmentNotFoundException, MozbuildObject

        build = MozbuildObject.from_environment()
        json_path = _os.path.join(build.topobjdir, "mozinfo.json")
        if _os.path.isfile(json_path):
            update(json_path)
            return json_path
    except ImportError:
        pass
    except (BuildEnvironmentNotFoundException, MozconfigFindException):
        pass

    for d in dirs:
        d = _os.path.abspath(d)
        json_path = _os.path.join(d, "mozinfo.json")
        if _os.path.isfile(json_path):
            update(json_path)
            return json_path

    # by default, exceptions are suppressed. Set this to True if otherwise
    # desired.
    if kwargs.get("raise_exception", False):
        raise IOError("mozinfo.json could not be found.")
    return None