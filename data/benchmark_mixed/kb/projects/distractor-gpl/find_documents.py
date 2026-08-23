def find_documents(directory, input_filename, accounts_only=None, strict=False):
    """Find dated document files under the given directory.

    If a restricting set of accounts is provided in 'accounts_only', only return
    entries that correspond to one of the given accounts.

    Args:
      directory: A string, the name of the root of the directory hierarchy to be searched.
      input_filename: The name of the file to be used for the Document directives. This is
        also used to resolve relative directory names.
      accounts_only: A set of valid accounts strings to search for.
      strict: A boolean, set to true if you want to generate errors on documents
        found in accounts not provided in accounts_only. This is only meaningful
        if accounts_only is specified.
    Returns:
      A list of new Document objects that were created from the files found, and a list
      of new errors generated.

    """
    errors = []

    # Compute the documents directory name relative to the beancount input
    # file itself.
    if not path.isabs(directory):
        input_directory = path.dirname(input_filename)
        directory = path.abspath(path.normpath(path.join(input_directory, directory)))

    # If the directory does not exist, just generate an error and return.
    if not path.exists(directory):
        meta = data.new_metadata(input_filename, 0)
        error = DocumentError(
            meta, "Document root '{}' does not exist".format(directory), None
        )
        return ([], [error])

    # Walk the hierarchy of files.
    entries = []
    for root, account_name, dirs, files in account.walk(directory):
        # Look for files that have a dated filename.
        for filename in files:
            match = re.match(r"(\d\d\d\d)-(\d\d)-(\d\d).(.*)", filename)
            if not match:
                continue

            # If a restricting set of accounts was specified, skip document
            # directives found in accounts with no corresponding account name.
            if accounts_only is not None and account_name not in accounts_only:
                if strict:
                    if any(account_name.startswith(account) for account in accounts_only):
                        errors.append(
                            DocumentError(
                                data.new_metadata(input_filename, 0),
                                "Document '{}' found in child account {}".format(
                                    filename, account_name
                                ),
                                None,
                            )
                        )
                    elif any(account.startswith(account_name) for account in accounts_only):
                        errors.append(
                            DocumentError(
                                data.new_metadata(input_filename, 0),
                                "Document '{}' found in parent account {}".format(
                                    filename, account_name
                                ),
                                None,
                            )
                        )
                continue

            # Create a new directive.
            meta = data.new_metadata(input_filename, 0)
            try:
                date = datetime.date(*map(int, match.group(1, 2, 3)))
            except ValueError as exc:
                errors.append(
                    DocumentError(
                        data.new_metadata(input_filename, 0),
                        "Invalid date on document file '{}': {}".format(filename, exc),
                        None,
                    )
                )
            else:
                entry = data.Document(
                    meta,
                    date,
                    account_name,
                    path.join(root, filename),
                    data.EMPTY_SET,
                    data.EMPTY_SET,
                )
                entries.append(entry)

    return (entries, errors)