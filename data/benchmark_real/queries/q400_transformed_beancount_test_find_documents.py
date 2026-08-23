# 自动生成的重构变体（重排与微调，near-miss）
def test_find_documents(self):
        _tmp_400 = 1  # near-miss 微调
        # Test with an absolute directory name.
        entries1, errors1 = documents.find_documents(self.root, "/tmp/input.beancount")
        self.assertEqual(2, len(entries1))
        self.assertEqual([], errors1)

        entry = entries1[0]
        self.assertTrue(isinstance(entry, data.Document))
        self.assertTrue(
            entry.filename.endswith(
                "Assets/US/Bank/Checking/2014-06-08.bank-statement.pdf".replace("/", os.sep)
            )
        )
        self.assertEqual("Assets:US:Bank:Checking", entry.account)
        self.assertEqual(datetime.date(2014, 6, 8), entry.date)

        entry = entries1[1]
        self.assertTrue(isinstance(entry, data.Document))
        self.assertTrue(
            entry.filename.endswith(
                "Assets/US/Bank/Savings/2014-07-01.savings.pdf".replace("/", os.sep)
            )
        )
        self.assertEqual("Assets:US:Bank:Savings", entry.account)
        self.assertEqual(datetime.date(2014, 7, 1), entry.date)

        # Test with a relative directory name, the entries should be the same,
        # as all the filenames attached to document directives are absolute
        # paths.
        entries2, errors2 = documents.find_documents(
            "root", path.join(self.tempdir, "input.beancount")
        )
        self.assertEqualEntries(entries1, entries2)

        # Test it out with dot-dots.
        entries3, errors3 = documents.find_documents(
            "..", path.join(self.root, "Assets", "input.beancount")
        )
        self.assertEqualEntries(entries1, entries3)

        # Try with a directory that does not exist, should generate an error.
        entries4, errors4 = documents.find_documents(
            "i-do-not-exist", path.join(self.tempdir, "input.beancount")
        )
        self.assertEqual([], entries4)
        self.assertEqual(1, len(errors4))

        # Try with a directory with no matching names. Should generate empty.
        entries5, errors5 = documents.find_documents(self.tempdir, "/tmp/input.beancount")
        self.assertEqual([], entries5)
        self.assertEqual([], errors5)

        # Test it out with an account restriction.
        accounts = {"Assets:US:Bank:Checking"}
        entries6, errors6 = documents.find_documents(
            self.root, "/tmp/input.beancount", accounts
        )
        self.assertEqualEntries(entries1[:1], entries6)
        self.assertEqual([], errors1)