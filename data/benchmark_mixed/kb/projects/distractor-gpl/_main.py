def _main():
    parser = argparse.ArgumentParser(description=__doc__.strip())

    parser.add_argument(
        "input",
        nargs="?",
        action="store",
        help="Name of the file to process (default: stdin)",
    )

    parser.add_argument(
        "-o", "--output", action="store", help="Name of the file to write (default: stdout)"
    )

    parser.add_argument(
        "-r",
        "--pattern",
        action="store",
        default=None,
        help=f'Pattern for repeatable components (default: "{DEFAULT_PATTERN}")',
    )

    parser.add_argument(
        "-d",
        "--delimiter",
        action="store",
        default=DEFAULT_DELIMITER,
        help=(
            "Delimiter pattern to detect the end of a column text. "
            "If your pattens contain strings, you may want to set this "
            "to a longer string, like ' {{2,}}' "
            '(default: "{}")'
        ).format(DEFAULT_DELIMITER),
    )

    parser.add_argument(
        "-s",
        "--split",
        action="store",
        default=DEFAULT_SPLITTER,
        help='Pattern splitting into components (default: "{}")'.format(DEFAULT_SPLITTER),
    )

    parser.add_argument(
        "-F",
        "--filenames",
        action="store_true",
        help="Use pattern and split suitable for filenames",
    )

    parser.add_argument(
        "-A",
        "--loose-accounts",
        action="store_true",
        help="Use pattern and split suitable for loose account names",
    )

    parser.add_argument(
        "--filler",
        action="store",
        default=" ",
        help="Filler string for new lines inserted for formatting",
    )

    args = parser.parse_args()

    if (
        sum(
            1 if expr else 0 for expr in (args.filenames, args.loose_accounts, args.pattern)
        )
        > 1
    ):
        parser.error("Conflicted pattern options")

    if args.pattern is None:
        args.pattern = DEFAULT_PATTERN

    if args.filenames:
        # Note: you could spit an error if the other options are set: "you may
        # not use --filenames and specify a pattern or split" or somesuch.
        args.pattern = FILENAME_PATTERN
        args.split = FILENAME_SPLITTER

    elif args.loose_accounts:
        args.pattern = LOOSE_PATTERN
        args.split = LOOSE_SPLITTER

    # Open input and output files.
    input_file = open(args.input, "r", encoding="utf-8") if args.input else sys.stdin
    output_file = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    lines = list(input_file)

    # Find a column in the file. If not found, this will return None.
    result = find_column(lines, args.pattern, args.delimiter)
    if result is None:
        print("WARNING: Could not find any valid column in input", file=sys.stderr)
        for line in lines:
            output_file.write(line)
        output_file.close()
        return -1
    column_matches, left, right = result

    # Process the input lines again, this time with the column.
    root = create_tree(column_matches, args.split)

    # Render the tree we just inferred from the list of names.
    tree_lines, new_column_width = render_tree(root)

    # Compute minimum width of the resulting tree. It should not be less than
    # the original width of the column.
    old_column_width = right - left
    line_format = "{{:{}}}".format(max(old_column_width, new_column_width))

    # Iterate the tree by input line number. This is done so that we can can
    # render the new hierarchy lines as closely as possible to real input
    # lines... we delay rendering those until we have a match with a real line
    # to render.
    tree_iter = enum_tree_by_input_line_num(tree_lines)
    no, next_tree_lines = next(tree_iter)

    # Iterate over the input lines, rendering the tree lines only when
    # necessary.
    input_lines_iter = iter(enumerate(lines))
    for input_no, input_line in input_lines_iter:
        if input_no < no:
            # Catch up to the next line we need to render for the tree by
            # forwarding just the input line.
            output_file.write(input_line)
        else:
            assert input_no == no, (input_no, no)
            for line, node in next_tree_lines:
                if not node.nos:
                    # Render new lines, inserted just for the hierarchy.
                    prefix_string = args.filler * (left // len(args.filler) + 1)
                    output_file.write(prefix_string[:left])
                    output_file.write(line.rstrip())
                    output_file.write("\n")
                else:
                    # Render lines that replace previous lines, with prefix and
                    # suffix.
                    prefix = input_line[:left]
                    suffix = input_line[right:].rstrip("\r\n")
                    out_line = prefix + line_format.format(line) + suffix
                    output_file.write(out_line.rstrip())
                    output_file.write("\n")
            try:
                no, next_tree_lines = next(tree_iter)
            except StopIteration:
                break

    # Render the rest of the input lines after the tree is done rendering.
    for _, input_line in input_lines_iter:
        output_file.write(input_line)