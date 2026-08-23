def test_set_fixed_precision(self):
        dcontext = display_context.DisplayContext()

        # Set fixed precision for USD
        dcontext.set_fixed_precision("USD", 2)

        # Update with numbers for USD and other currencies.
        dcontext.update(Decimal("123.456"), "USD")
        dcontext.update(Decimal("1000"), "USD")
        dcontext.update(Decimal("-987.654321"), "USD")

        dcontext.update(Decimal("1.2345"), "EUR")
        dcontext.update(Decimal("764"), "EUR")
        dcontext.update(Decimal("0.00000125"), "EUR")

        dcontext.update(Decimal("5000.0"), "CAD")

        # Test USD formatting with fixed precision (MOST_COMMON).
        dformat_usd_common = dcontext.build(
            alignment=Align.NATURAL, precision=Precision.MOST_COMMON
        )
        self.assertEqual(dformat_usd_common.format(Decimal("123.456"), "USD"), "123.46")
        self.assertEqual(
            dformat_usd_common.format(Decimal("-987.654321"), "USD"), "-987.65"
        )
        self.assertEqual(dformat_usd_common.format(Decimal("1000"), "USD"), "1000.00")
        self.assertEqual(dformat_usd_common.format(Decimal("0.001"), "USD"), "0.00")

        # Test USD formatting with fixed precision (MAXIMUM) - should be the
        # same as MOST_COMMON
        dformat_usd_max = dcontext.build(
            alignment=Align.NATURAL, precision=Precision.MAXIMUM
        )
        self.assertEqual(dformat_usd_max.format(Decimal("123.456"), "USD"), "123.46")
        self.assertEqual(dformat_usd_max.format(Decimal("-987.654321"), "USD"), "-987.65")
        self.assertEqual(dformat_usd_max.format(Decimal("1000"), "USD"), "1000.00")
        self.assertEqual(dformat_usd_max.format(Decimal("0.001"), "USD"), "0.00")

        # Test EUR formatting (learned precision)
        dformat_eur = dcontext.build(alignment=Align.NATURAL)
        self.assertEqual(dformat_eur.format(Decimal("1.2345"), "EUR"), "1.23450000")
        self.assertEqual(dformat_eur.format(Decimal("0.00000125"), "EUR"), "0.00000125")

        # Test CAD formatting (learned precision)
        dformat_cad = dcontext.build(alignment=Align.NATURAL)
        self.assertEqual(dformat_cad.format(Decimal("5000.0"), "CAD"), "5000.0")

        # Test quantize with fixed precision
        self.assertEqual(dcontext.quantize(Decimal("123.456789"), "USD"), Decimal("123.46"))
        self.assertEqual(dcontext.quantize(Decimal("99.999"), "USD"), Decimal("100.00"))
        self.assertEqual(dcontext.quantize(Decimal("0.001"), "USD"), Decimal("0.00"))

        # Test quantize with learned precision for EUR (most common is 0)
        self.assertEqual(dcontext.quantize(Decimal("1.2345"), "EUR"), Decimal("1.2345000"))

        # Test that setting fixed precision for a currency replaces its context.
        dcontext_replace = display_context.DisplayContext()
        dcontext_replace.update(
            Decimal("1.23456"), "XYZ"
        )  # This would normally lead to 5 or 6 decimal places
        self.assertIsInstance(dcontext_replace.ccontexts["XYZ"], _CurrencyContext)
        dcontext_replace.set_fixed_precision("XYZ", 3)
        self.assertIsInstance(dcontext_replace.ccontexts["XYZ"], _FixedPrecisionContext)
        dformat_xyz = dcontext_replace.build(alignment=Align.NATURAL)
        self.assertEqual(dformat_xyz.format(Decimal("1.23456"), "XYZ"), "1.235")