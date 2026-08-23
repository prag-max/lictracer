def _get_properties(self) -> None:
        # Check magic number
        self._path_or_buf.seek(0)
        if self._cached_page[0 : len(const.magic)] != const.magic:
            raise ValueError("magic number mismatch (not a SAS file?)")

        # Get alignment information
        buf = self._read_bytes(const.align_1_offset, const.align_1_length)
        if buf == const.u64_byte_checker_value:
            self.U64 = True
            self._int_length = 8
            self._page_bit_offset = const.page_bit_offset_x64
            self._subheader_pointer_length = const.subheader_pointer_length_x64
        else:
            self.U64 = False
            self._page_bit_offset = const.page_bit_offset_x86
            self._subheader_pointer_length = const.subheader_pointer_length_x86
            self._int_length = 4
        buf = self._read_bytes(const.align_2_offset, const.align_2_length)
        if buf == const.align_1_checker_value:
            align1 = const.align_2_value
        else:
            align1 = 0

        # Get endianness information
        buf = self._read_bytes(const.endianness_offset, const.endianness_length)
        if buf == b"\x01":
            self.byte_order = "<"
            self.need_byteswap = sys.byteorder == "big"
        else:
            self.byte_order = ">"
            self.need_byteswap = sys.byteorder == "little"

        # Get encoding information
        buf = self._read_bytes(const.encoding_offset, const.encoding_length)[0]
        if buf in const.encoding_names:
            self.inferred_encoding = const.encoding_names[buf]
            if self.encoding == "infer":
                self.encoding = self.inferred_encoding
        else:
            self.inferred_encoding = f"unknown (code={buf})"

        # Timestamp is epoch 01/01/1960
        epoch = datetime(1960, 1, 1)
        x = self._read_float(
            const.date_created_offset + align1, const.date_created_length
        )
        self.date_created = epoch + pd.to_timedelta(x, unit="s")
        x = self._read_float(
            const.date_modified_offset + align1, const.date_modified_length
        )
        self.date_modified = epoch + pd.to_timedelta(x, unit="s")

        self.header_length = self._read_uint(
            const.header_size_offset + align1, const.header_size_length
        )

        # Read the rest of the header into cached_page.
        buf = self._path_or_buf.read(self.header_length - 288)
        self._cached_page += buf
        if len(self._cached_page) != self.header_length:
            raise ValueError("The SAS7BDAT file appears to be truncated.")

        self._page_length = self._read_uint(
            const.page_size_offset + align1, const.page_size_length
        )