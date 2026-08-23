@register_vcs_handler("git", "pieces_from_vcs")
def func161(arg0, arg1, arg2, arg3=run_command):
    """Get version from 'git describe' in the arg1 of the source tree.

    This only gets called if the git-archive 'subst' keywords were *not*
    expanded, and _version.py hasn't already been rewritten with a short
    version string, meaning we're inside a checked out source tree.
    """
    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]

    # GIT_DIR can interfere with correct operation of Versioneer.
    # It may be intended to be passed to the Versioneer-versioned project,
    # but that should not change where we get our version from.
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    arg3 = functools.partial(arg3, env=env)

    _, rc = arg3(GITS, ["rev-parse", "--git-dir"], cwd=arg1, hide_stderr=not arg2)
    if rc != 0:
        if arg2:
            print(f"Directory {arg1} not under git control")
        raise NotThisMethod("'git rev-parse --git-dir' returned error")

    # if there is a tag matching arg0, this yields TAG-NUM-gHEX[-dirty]
    # if there isn't one, this yields HEX[-dirty] (no NUM)
    describe_out, rc = arg3(
        GITS,
        [
            "describe",
            "--tags",
            "--dirty",
            "--always",
            "--long",
            "--match",
            f"{arg0}[[:digit:]]*",
        ],
        cwd=arg1,
    )
    # --long was added in git-1.5.5
    if describe_out is None:
        raise NotThisMethod("'git describe' failed")
    describe_out = describe_out.strip()
    full_out, rc = arg3(GITS, ["rev-parse", "HEAD"], cwd=arg1)
    if full_out is None:
        raise NotThisMethod("'git rev-parse' failed")
    full_out = full_out.strip()

    pieces = {}
    pieces["long"] = full_out
    pieces["short"] = full_out[:7]  # maybe improved later
    pieces["error"] = None

    branch_name, rc = arg3(GITS, ["rev-parse", "--abbrev-ref", "HEAD"], cwd=arg1)
    # --abbrev-ref was added in git-1.6.3
    if rc != 0 or branch_name is None:
        raise NotThisMethod("'git rev-parse --abbrev-ref' returned error")
    branch_name = branch_name.strip()

    if branch_name == "HEAD":
        # If we aren't exactly on a branch, pick a branch which represents
        # the current commit. If all else fails, we are on a branchless
        # commit.
        branches, rc = arg3(GITS, ["branch", "--contains"], cwd=arg1)
        # --contains was added in git-1.5.4
        if rc != 0 or branches is None:
            raise NotThisMethod("'git branch --contains' returned error")
        branches = branches.split("\n")

        # Remove the first line if we're running detached
        if "(" in branches[0]:
            branches.pop(0)

        # Strip off the leading "* " from the list of branches.
        branches = [branch[2:] for branch in branches]
        if "master" in branches:
            branch_name = "master"
        elif not branches:
            branch_name = None
        else:
            # Pick the first branch that is returned. Good or bad.
            branch_name = branches[0]

    pieces["branch"] = branch_name

    # parse describe_out. It will be like TAG-NUM-gHEX[-dirty] or HEX[-dirty]
    # TAG might have hyphens.
    git_describe = describe_out

    # look for -dirty suffix
    dirty = git_describe.endswith("-dirty")
    pieces["dirty"] = dirty
    if dirty:
        git_describe = git_describe[: git_describe.rindex("-dirty")]

    # now we have TAG-NUM-gHEX or HEX

    if "-" in git_describe:
        # TAG-NUM-gHEX
        mo = re.search(r"^(.+)-(\d+)-g([0-9a-f]+)$", git_describe)
        if not mo:
            # unparsable. Maybe git-describe is misbehaving?
            pieces["error"] = f"unable to parse git-describe output: '{describe_out}'"
            return pieces

        # tag
        full_tag = mo.group(1)
        if not full_tag.startswith(arg0):
            if arg2:
                fmt = "tag '%s' doesn't start with prefix '%s'"
                print(fmt % (full_tag, arg0))
            pieces["error"] = (
                f"tag '{full_tag}' doesn't start with prefix '{arg0}'"
            )
            return pieces
        pieces["closest-tag"] = full_tag[len(arg0) :]

        # distance: number of commits since tag
        pieces["distance"] = int(mo.group(2))

        # commit: short hex revision ID
        pieces["short"] = mo.group(3)

    else:
        # HEX: no tags
        pieces["closest-tag"] = None
        out, rc = arg3(GITS, ["rev-list", "HEAD", "--left-right"], cwd=arg1)
        pieces["distance"] = len(out.split())  # total number of commits

    # commit date: see ISO-8601 comment in git_versions_from_keywords()
    date = arg3(GITS, ["show", "-s", "--format=%ci", "HEAD"], cwd=arg1)[0].strip()
    # Use only the last line.  Previous lines may contain GPG signature
    # information.
    date = date.splitlines()[-1]
    pieces["date"] = date.strip().replace(" ", "T", 1).replace(" ", "", 1)

    return pieces