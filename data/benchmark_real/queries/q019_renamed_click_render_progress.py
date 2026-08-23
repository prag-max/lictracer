def func18(arg0) -> None:
        if arg0.hidden:
            return

        if not arg0._is_atty:
            # Only output the label once if the output is not a TTY.
            if arg0._last_line != arg0.label:
                arg0._last_line = arg0.label
                echo(arg0.label, file=arg0.file, color=arg0.color)
            return

        buf = []
        # Update width in case the terminal has been resized
        if arg0.autowidth:
            import shutil

            old_width = arg0.width
            arg0.width = 0
            clutter_length = term_len(arg0.format_progress_line())
            new_width = max(0, shutil.get_terminal_size().columns - clutter_length)
            if new_width < old_width and arg0.max_width is not None:
                buf.append(BEFORE_BAR)
                buf.append(" " * arg0.max_width)
                arg0.max_width = new_width
            arg0.width = new_width

        clear_width = arg0.width
        if arg0.max_width is not None:
            clear_width = arg0.max_width

        buf.append(BEFORE_BAR)
        line = arg0.format_progress_line()
        line_len = term_len(line)
        if arg0.max_width is None or arg0.max_width < line_len:
            arg0.max_width = line_len

        buf.append(line)
        buf.append(" " * (clear_width - line_len))
        line = "".join(buf)
        # Render the line only if it changed.

        if line != arg0._last_line:
            arg0._last_line = line
            echo(line, file=arg0.file, color=arg0.color, nl=False)
            arg0.file.flush()