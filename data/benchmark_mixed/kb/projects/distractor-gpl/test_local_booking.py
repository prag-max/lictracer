def test_local_booking(self):
        fileloc = data.new_metadata("<local>", 0)
        date = datetime.date.today()
        txn = data.Transaction(
            fileloc,
            date,
            "*",
            None,
            "Narration",
            data.EMPTY_SET,
            data.EMPTY_SET,
            [
                data.Posting(
                    "Assets:Something",
                    MISSING,
                    position.CostSpec(MISSING, None, MISSING, MISSING, MISSING, MISSING),
                    MISSING,
                    None,
                    None,
                )
            ],
        )
        expected_txn = data.Transaction(
            fileloc,
            date,
            "*",
            None,
            "Narration",
            data.EMPTY_SET,
            data.EMPTY_SET,
            [
                data.Posting(
                    "Assets:Something",
                    None,
                    position.Cost(None, None, None, None),
                    None,
                    None,
                    None,
                )
            ],
        )
        actual_txn = cmptest._local_booking(txn)
        self.assertEqual(actual_txn, expected_txn)

        txn = data.Transaction(
            fileloc,
            date,
            "*",
            None,
            "Narration",
            data.EMPTY_SET,
            data.EMPTY_SET,
            [
                data.Posting(
                    "Assets:Something",
                    amount.Amount(MISSING, MISSING),
                    position.CostSpec(MISSING, None, MISSING, MISSING, MISSING, MISSING),
                    amount.Amount(MISSING, MISSING),
                    None,
                    None,
                )
            ],
        )
        expected_txn = data.Transaction(
            fileloc,
            date,
            "*",
            None,
            "Narration",
            data.EMPTY_SET,
            data.EMPTY_SET,
            [
                data.Posting(
                    "Assets:Something",
                    amount.Amount(None, None),
                    position.Cost(None, None, None, None),
                    amount.Amount(None, None),
                    None,
                    None,
                )
            ],
        )
        actual_txn = cmptest._local_booking(txn)
        self.assertEqual(actual_txn, expected_txn)