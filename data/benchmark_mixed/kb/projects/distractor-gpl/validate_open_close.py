def validate_open_close(entries, unused_options_map):
    """Check constraints on open and close directives themselves.

    This method checks two kinds of constraints:

    1. An open or a close directive may only show up once for each account. If a
       duplicate is detected, an error is generated.

    2. Close directives may only appear if an open directive has been seen
       previously (chronologically).

    3. The date of close directives must be strictly greater than their
       corresponding open directive.

    Args:
      entries: A list of directives.
      unused_options_map: An options map.
    Returns:
      A list of new errors, if any were found.
    """
    errors = []
    open_map = {}
    close_map = {}
    for entry in entries:
        if isinstance(entry, Open):
            if entry.account in open_map:
                errors.append(
                    ValidationError(
                        entry.meta,
                        "Duplicate open directive for {}".format(entry.account),
                        entry,
                    )
                )
            else:
                open_map[entry.account] = entry

        elif isinstance(entry, Close):
            if entry.account in close_map:
                errors.append(
                    ValidationError(
                        entry.meta,
                        "Duplicate close directive for {}".format(entry.account),
                        entry,
                    )
                )
            else:
                try:
                    open_entry = open_map[entry.account]
                    if entry.date < open_entry.date:
                        errors.append(
                            ValidationError(
                                entry.meta,
                                "Internal error: closing date for {} "
                                "appears before opening date".format(entry.account),
                                entry,
                            )
                        )
                except KeyError:
                    errors.append(
                        ValidationError(
                            entry.meta,
                            "Unopened account {} is being closed".format(entry.account),
                            entry,
                        )
                    )

                close_map[entry.account] = entry

    return errors