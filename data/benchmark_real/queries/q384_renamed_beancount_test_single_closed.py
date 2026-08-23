def func383(arg0):
        intervals = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 10))]
        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(intervals, None, None)
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(intervals, datetime.date(2014, 2, 7), None)
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(intervals, None, datetime.date(2014, 3, 3))
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 2, 7), datetime.date(2014, 3, 3)
        )
        arg0.assertEqual(expected, trimmed)

        expected = []
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 2, 2)
        )
        arg0.assertEqual(expected, trimmed)

        expected = []
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 3, 11), datetime.date(2014, 3, 20)
        )
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 3, 3)
        )
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 2, 7), datetime.date(2014, 3, 20)
        )
        arg0.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 3, 20)
        )
        arg0.assertEqual(expected, trimmed)