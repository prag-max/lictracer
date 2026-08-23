def test_single_closed(self):
        intervals = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(intervals, None, None)
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(intervals, datetime.date(2014, 2, 7), None)
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(intervals, None, datetime.date(2014, 3, 3))
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 2, 7), datetime.date(2014, 3, 3)
        )
        self.assertEqual(expected, trimmed)

        expected = []
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 2, 2)
        )
        self.assertEqual(expected, trimmed)

        expected = []
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 3, 11), datetime.date(2014, 3, 20)
        )
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 3))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 3, 3)
        )
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 7), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 2, 7), datetime.date(2014, 3, 20)
        )
        self.assertEqual(expected, trimmed)

        expected = [(datetime.date(2014, 2, 3), datetime.date(2014, 3, 10))]
        trimmed = lifetimes.trim_intervals(
            intervals, datetime.date(2014, 1, 2), datetime.date(2014, 3, 20)
        )
        self.assertEqual(expected, trimmed)