def test_from_string(self):
        inv = inventory.from_string("10 USD")
        self.assertEqual(Inventory([Position(A("10 USD"))]), inv)

        inv = inventory.from_string(" 10.00  USD ")
        self.assertEqual(Inventory([Position(A("10 USD"))]), inv)

        inv = inventory.from_string("1 USD, 2 CAD")
        self.assertEqual(Inventory([Position(A("1 USD")), Position(A("2 CAD"))]), inv)

        inv = inventory.from_string("2.2 HOOL {532.43 USD}, 3.413 EUR")
        self.assertEqual(
            Inventory(
                [
                    Position(A("2.2 HOOL"), Cost(D("532.43"), "USD", None, None)),
                    Position(A("3.413 EUR")),
                ]
            ),
            inv,
        )

        inv = inventory.from_string(
            "2.2 HOOL {532.43 USD}, 2.3 HOOL {564.00 USD, 2015-07-14}, 3.413 EUR"
        )
        self.assertEqual(
            Inventory(
                [
                    Position(A("2.2 HOOL"), Cost(D("532.43"), "USD", None, None)),
                    Position(
                        A("2.3 HOOL"),
                        Cost(D("564.00"), "USD", datetime.date(2015, 7, 14), None),
                    ),
                    Position(A("3.413 EUR")),
                ]
            ),
            inv,
        )

        inv = inventory.from_string("1.1 HOOL {500.00 # 11.00 USD}, 100 CAD")
        self.assertEqual(
            Inventory(
                [
                    Position(A("1.1 HOOL"), Cost(D("510.00"), "USD", None, None)),
                    Position(A("100 CAD")),
                ]
            ),
            inv,
        )