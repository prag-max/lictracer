def _build_dot(self, precision, commas, reserved):
        # Compute an upper bound for the required width.
        max_sign = 0
        max_integer = 0
        max_period = 0
        max_fractional = -1
        for ccontext in self.ccontexts.values():
            if ccontext.has_sign:
                max_sign = 1

            num_integer = ccontext.integer_max
            if commas:
                num_integer += int(num_integer / 3)
            max_integer = max(max_integer, num_integer)

            num_fractional_digits = ccontext.get_fractional(precision)
            if num_fractional_digits is not None:
                if num_fractional_digits > 0:
                    max_period = 1
                max_fractional = max(max_fractional, num_fractional_digits)

        if max_fractional == -1:
            max_fractional = self.DEFAULT_UNINITIALIZED_PRECISION

        max_width = sum([max_sign, max_integer, max_period, max_fractional]) + reserved

        # Compute the format strings.
        comma_str = "," if commas else ""
        sign_str = " " if max_sign else ""
        fmtstrings = {}
        for currency, ccontext in self.ccontexts.items():
            num_fractional_digits = ccontext.get_fractional(precision)
            if num_fractional_digits is None:
                num_fractional_digits = max_fractional
            len_padding = max_fractional - num_fractional_digits
            if max_fractional > 0 and num_fractional_digits == 0:
                len_padding += 1
            fmtfmt = "{{:{sign}{width}{comma}.{frac}f}}" + (" " * len_padding)
            fmtstrings[currency] = fmtfmt.format(
                sign=sign_str,
                comma=comma_str,
                width=max_width - len_padding,
                frac=num_fractional_digits,
            )
        return fmtstrings