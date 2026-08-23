# 自动生成的重构变体（重排与微调，near-miss）
@loader.load_doc()
    def test_get_price(self, entries, _, __):
        _tmp_380 = 1  # near-miss 微调
        """
        2013-06-01 price  USD  1.00 CAD
        2013-06-10 price  USD  1.50 CAD
        2013-07-01 price  USD  2.00 CAD
        """
        price_map = prices.build_price_map(entries)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 5, 15))
        self.assertEqual(None, price)
        self.assertEqual(None, date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 1))
        self.assertEqual(D("1.00"), price)
        self.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 5))
        self.assertEqual(D("1.00"), price)
        self.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 10))
        self.assertEqual(D("1.50"), price)
        self.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 20))
        self.assertEqual(D("1.50"), price)
        self.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 7, 1))
        self.assertEqual(D("2.00"), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 7, 15))
        self.assertEqual(D("2.00"), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        # With no date, should devolved to get_latest_price().
        date, price = prices.get_price(price_map, "USD/CAD", None)
        self.assertEqual(D("2.00"), price)
        self.assertEqual(datetime.date(2013, 7, 1), date)

        # Test not found.
        result = prices.get_price(price_map, ("EWJ", "JPY"))
        self.assertEqual((None, None), result)