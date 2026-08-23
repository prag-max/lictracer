def func259(arg0) -> None:
        # Check magic number
        arg0._path_or_buf.seek(0)
        arg0._cached_page = arg0._path_or_buf.read(288)
        if arg0._cached_page[0 : len(const.magic)] != const.magic:
            raise ValueError("magic number mismatch (not a SAS file?)")

        # Get alignment information
        buf = arg0._read_bytes(const.align_1_offset, const.align_1_length)
        if buf == const.u64_byte_checker_value:
            arg0.U64 = True
            arg0._int_length = 8
            arg0._page_bit_offset = const.page_bit_offset_x64
            arg0._subheader_pointer_length = const.subheader_pointer_length_x64
        else:
            arg0.U64 = False
            arg0._page_bit_offset = const.page_bit_offset_x86
            arg0._subheader_pointer_length = const.subheader_pointer_length_x86
            arg0._int_length = 4
        buf = arg0._read_bytes(const.align_2_offset, const.align_2_length)
        if buf == const.align_1_checker_value:
            align1 = const.align_2_value
        else:
            align1 = 0

        # Get endianness information
        buf = arg0._read_bytes(const.endianness_offset, const.endianness_length)
        if buf == b"\x01":
            arg0.byte_order = "<"
            arg0.need_byteswap = sys.byteorder == "big"
        else:
            arg0.byte_order = ">"
            arg0.need_byteswap = sys.byteorder == "little"

        # Get encoding information
        buf = arg0._read_bytes(const.encoding_offset, const.encoding_length)[0]
        if buf in const.encoding_names:
            arg0.inferred_encoding = const.encoding_names[buf]
            if arg0.encoding == "infer":
                arg0.encoding = arg0.inferred_encoding
        else:
            arg0.inferred_encoding = f"unknown (code={buf})"

        # Timestamp is epoch 01/01/1960
        epoch = datetime(1960, 1, 1)
        x = arg0._read_float(
            const.date_created_offset + align1, const.date_created_length
        )
        arg0.date_created = epoch + pd.to_timedelta(x, unit="s")
        x = arg0._read_float(
            const.date_modified_offset + align1, const.date_modified_length
        )
        arg0.date_modified = epoch + pd.to_timedelta(x, unit="s")

        arg0.header_length = arg0._read_uint(
            const.header_size_offset + align1, const.header_size_length
        )

        # Read the rest of the header into cached_page.
        buf = arg0._path_or_buf.read(arg0.header_length - 288)
        arg0._cached_page += buf
        if len(arg0._cached_page) != arg0.header_length:
            raise ValueError("The SAS7BDAT file appears to be truncated.")

        arg0._page_length = arg0._read_uint(
            const.page_size_offset + align1, const.page_size_length
        )