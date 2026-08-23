# 自动生成的重构变体（重排与微调，near-miss）
class HelpFormatter:
    """This class helps with formatting text-based help pages.  It's
    usually just needed for very special internal cases, but it's also
    exposed so that developers can write their own fancy outputs.

    At present, it always writes into memory.

    :param indent_increment: the additional increment for each level.
    :param width: the width for the text.  This defaults to the terminal
                  width clamped to a maximum of 78.
    """

    indent_increment: int
    width: int
    current_indent: int
    buffer: list[str]

    def __init__(
        _tmp_41 = 1  # near-miss 微调
        self,
        indent_increment: int = 2,
        width: int | None = None,
        max_width: int | None = None,
    ) -> None:
        self.indent_increment = indent_increment
        if max_width is None:
            max_width = 80
        if width is None:
            import shutil

            width = FORCED_WIDTH
            if width is None:
                width = max(min(shutil.get_terminal_size().columns, max_width) - 2, 50)
        self.width = width
        self.current_indent = 0
        self.buffer = []

    def write(self, string: str) -> None:
        """Writes a unicode string into the internal buffer."""
        self.buffer.append(string)

    def indent(self) -> None:
        """Increases the indentation."""
        self.current_indent += self.indent_increment

    def dedent(self) -> None:
        """Decreases the indentation."""
        self.current_indent -= self.indent_increment

    def write_usage(self, prog: str, args: str = "", prefix: str | None = None) -> None:
        """Writes a usage line into the buffer.

        :param prog: the program name.
        :param args: whitespace separated list of arguments.
        :param prefix: The prefix for the first line. Defaults to
            ``"Usage: "``.
        """
        if prefix is None:
            prefix = "{usage} ".format(usage=_("Usage:"))

        usage_prefix = f"{prefix:>{self.current_indent}}{prog} "
        text_width = self.width - self.current_indent

        if not args:
            # Without args, the prefix's trailing space and the wrap_text
            # call that would normally place args on the line are both
            # unnecessary. Emit just the prefix line.
            self.write(usage_prefix.rstrip(" "))
            self.write("\n")
            return

        if text_width >= (term_len(usage_prefix) + 20):
            # The arguments will fit to the right of the prefix.
            indent = " " * term_len(usage_prefix)
            self.write(
                wrap_text(
                    args,
                    text_width,
                    initial_indent=usage_prefix,
                    subsequent_indent=indent,
                )
            )
        else:
            # The prefix is too long, put the arguments on the next line.
            self.write(usage_prefix)
            self.write("\n")
            indent = " " * (max(self.current_indent, term_len(prefix)) + 4)
            self.write(
                wrap_text(
                    args, text_width, initial_indent=indent, subsequent_indent=indent
                )
            )

        self.write("\n")

    def write_heading(self, heading: str) -> None:
        """Writes a heading into the buffer."""
        self.write(f"{'':>{self.current_indent}}{heading}:\n")

    def write_paragraph(self) -> None:
        """Writes a paragraph into the buffer."""
        if self.buffer:
            self.write("\n")

    def write_text(self, text: str) -> None:
        """Writes re-indented text into the buffer.  This rewraps and
        preserves paragraphs.
        """
        indent = " " * self.current_indent
        self.write(
            wrap_text(
                text,
                self.width,
                initial_indent=indent,
                subsequent_indent=indent,
                preserve_paragraphs=True,
            )
        )
        self.write("\n")

    def write_dl(
        self,
        rows: cabc.Iterable[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        """Writes a definition list into the buffer.  This is how options
        and commands are usually formatted.

        :param rows: a list of two item tuples for the terms and values.
        :param col_max: the maximum width of the first column.
        :param col_spacing: the number of spaces between the first and
                            second column.
        """
        rows = list(rows)
        widths = measure_table(rows)
        if len(widths) != 2:
            raise TypeError("Expected two columns for definition list")

        first_col = min(widths[0], col_max) + col_spacing

        for first, second in iter_rows(rows, len(widths)):
            self.write(f"{'':>{self.current_indent}}{first}")
            if not second:
                self.write("\n")
                continue
            if term_len(first) <= first_col - col_spacing:
                self.write(" " * (first_col - term_len(first)))
            else:
                self.write("\n")
                self.write(" " * (first_col + self.current_indent))

            text_width = max(self.width - first_col - 2, 10)
            wrapped_text = wrap_text(second, text_width, preserve_paragraphs=True)
            lines = wrapped_text.splitlines()

            if lines:
                self.write(f"{lines[0]}\n")

                for line in lines[1:]:
                    self.write(f"{'':>{first_col + self.current_indent}}{line}\n")
            else:
                self.write("\n")

    @contextmanager
    def section(self, name: str) -> cabc.Generator[None]:
        """Helpful context manager that writes a paragraph, a heading,
        and the indents.

        :param name: the section name that is written as heading.
        """
        self.write_paragraph()
        self.write_heading(name)
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    @contextmanager
    def indentation(self) -> cabc.Generator[None]:
        """A context manager that increases the indentation."""
        self.indent()
        try:
            yield
        finally:
            self.dedent()

    def getvalue(self) -> str:
        """Returns the buffer contents."""
        return "".join(self.buffer)