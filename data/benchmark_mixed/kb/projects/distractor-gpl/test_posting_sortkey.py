def test_posting_sortkey(self):
        entries = self.create_sort_data()
        txn_postings = [
            (
                data.TxnPosting(entry, entry.postings[0])
                if isinstance(entry, data.Transaction)
                else entry
            )
            for entry in entries
        ]
        sorted_txn_postings = sorted(txn_postings, key=data.posting_sortkey)

        self.assertEqual(
            [
                data.TxnPosting,
                data.Open,
                data.Balance,
                data.TxnPosting,
                data.TxnPosting,
                data.Close,
                data.TxnPosting,
            ],
            list(map(type, sorted_txn_postings)),
        )

        self.assertEqual(
            [900, 1002, 1001, 1008, 1009, 1000, 1100],
            [entry.meta["lineno"] for entry in map(data.get_entry, sorted_txn_postings)],
        )