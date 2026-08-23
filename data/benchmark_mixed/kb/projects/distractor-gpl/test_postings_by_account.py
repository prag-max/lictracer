@loader.load_doc()
    def test_postings_by_account(self, entries, errors, _):
        """
        option "plugin_processing_mode" "raw"

        2012-01-01 open Expenses:Restaurant
        2012-01-01 open Expenses:Movie
        2012-01-01 open Assets:Cash
        2012-01-01 open Liabilities:CreditCard
        2012-01-01 open Equity:Opening-Balances

        2012-01-15 pad Liabilities:CreditCard Equity:Opening-Balances

        2012-03-01 * "Food"
          Expenses:Restaurant     100 CAD
          Assets:Cash            -100 CAD

        2012-03-10 * "Food again"
          Expenses:Restaurant      80 CAD
          Liabilities:CreditCard  -80 CAD

        ;; Two postings on the same account.
        2012-03-15 * "Two Movies"
          Expenses:Movie           10 CAD
          Expenses:Movie           10 CAD
          Liabilities:CreditCard  -20 CAD

        2012-03-20 note Liabilities:CreditCard "Called Amex, asked about 100 CAD dinner"

        2012-03-28 document Liabilities:CreditCard "march-statement.pdf"

        2013-04-01 balance Liabilities:CreditCard   204 CAD

        2014-01-01 close Liabilities:CreditCard
        """
        self.assertEqual(0, len(errors))

        txn_postings_map = realization.postings_by_account(entries)
        self.assertTrue(isinstance(txn_postings_map, dict))

        self.assertEqual(
            [data.Open, data.TxnPosting], list(map(type, txn_postings_map["Assets:Cash"]))
        )

        self.assertEqual(
            [data.Open, data.TxnPosting, data.TxnPosting],
            list(map(type, txn_postings_map["Expenses:Restaurant"])),
        )

        self.assertEqual(
            [data.Open, data.TxnPosting, data.TxnPosting],
            list(map(type, txn_postings_map["Expenses:Movie"])),
        )

        self.assertEqual(
            [
                data.Open,
                data.Pad,
                data.TxnPosting,
                data.TxnPosting,  # data.TxnPosting,
                data.Note,
                data.Document,
                data.Balance,
                data.Close,
            ],
            list(map(type, txn_postings_map["Liabilities:CreditCard"])),
        )

        self.assertEqual(
            [data.Open, data.Pad],
            list(map(type, txn_postings_map["Equity:Opening-Balances"])),
        )