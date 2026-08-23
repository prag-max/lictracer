def func235(arg0, arg1: int, arg2: int) -> None:
        int_len = arg0._int_length
        text_subheader_format = (
            arg1 + const.column_format_text_subheader_index_offset + 3 * int_len
        )
        col_format_offset = arg1 + const.column_format_offset_offset + 3 * int_len
        col_format_len = arg1 + const.column_format_length_offset + 3 * int_len
        text_subheader_label = (
            arg1 + const.column_label_text_subheader_index_offset + 3 * int_len
        )
        col_label_offset = arg1 + const.column_label_offset_offset + 3 * int_len
        col_label_len = arg1 + const.column_label_length_offset + 3 * int_len

        x = arg0._read_uint(
            text_subheader_format, const.column_format_text_subheader_index_length
        )
        format_idx = min(x, len(arg0.column_names_raw) - 1)

        format_start = arg0._read_uint(
            col_format_offset, const.column_format_offset_length
        )
        format_len = arg0._read_uint(col_format_len, const.column_format_length_length)

        label_idx = arg0._read_uint(
            text_subheader_label, const.column_label_text_subheader_index_length
        )
        label_idx = min(label_idx, len(arg0.column_names_raw) - 1)

        label_start = arg0._read_uint(
            col_label_offset, const.column_label_offset_length
        )
        label_len = arg0._read_uint(col_label_len, const.column_label_length_length)

        label_names = arg0.column_names_raw[label_idx]
        column_label = arg0._convert_header_text(
            label_names[label_start : label_start + label_len]
        )
        format_names = arg0.column_names_raw[format_idx]
        column_format = arg0._convert_header_text(
            format_names[format_start : format_start + format_len]
        )
        current_column_number = len(arg0.columns)

        col = _Column(
            current_column_number,
            arg0.column_names[current_column_number],
            column_label,
            column_format,
            arg0._column_types[current_column_number],
            arg0._column_data_lengths[current_column_number],
        )

        arg0.column_formats.append(column_format)
        arg0.columns.append(col)