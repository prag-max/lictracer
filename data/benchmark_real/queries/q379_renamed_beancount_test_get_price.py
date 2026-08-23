@loader.load_doc()
    def func378(arg0, arg1, arg2, arg3):
        """
        2013-06-01 price  USD  1.00 CAD
        2013-06-10 price  USD  1.50 CAD
        2013-07-01 price  USD  2.00 CAD
        """
        price_map = prices.build_price_map(arg1)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 5, 15))
        arg0.assertEqual(None, price)
        arg0.assertEqual(None, date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 1))
        arg0.assertEqual(D("1.00"), price)
        arg0.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 5))
        arg0.assertEqual(D("1.00"), price)
        arg0.assertEqual(datetime.date(2013, 6, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 10))
        arg0.assertEqual(D("1.50"), price)
        arg0.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 6, 20))
        arg0.assertEqual(D("1.50"), price)
        arg0.assertEqual(datetime.date(2013, 6, 10), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 7, 1))
        arg0.assertEqual(D("2.00"), price)
        arg0.assertEqual(datetime.date(2013, 7, 1), date)

        date, price = prices.get_price(price_map, "USD/CAD", datetime.date(2013, 7, 15))
        arg0.assertEqual(D("2.00"), price)
        arg0.assertEqual(datetime.date(2013, 7, 1), date)

        # With no date, should devolved to get_latest_price().
        date, price = prices.get_price(price_map, "USD/CAD", None)
        arg0.assertEqual(D("2.00"), price)
        arg0.assertEqual(datetime.date(2013, 7, 1), date)

        # Test not found.
        result = prices.get_price(price_map, ("EWJ", "JPY"))
        arg0.assertEqual((None, None), result)