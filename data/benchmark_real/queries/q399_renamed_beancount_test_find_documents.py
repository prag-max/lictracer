def func398(arg0):
        # Test with an absolute directory name.
        entries1, errors1 = documents.find_documents(arg0.root, "/tmp/input.beancount")
        arg0.assertEqual(2, len(entries1))
        arg0.assertEqual([], errors1)

        entry = entries1[0]
        arg0.assertTrue(isinstance(entry, data.Document))
        arg0.assertTrue(
            entry.filename.endswith(
                "Assets/US/Bank/Checking/2014-06-08.bank-statement.pdf".replace("/", os.sep)
            )
        )
        arg0.assertEqual("Assets:US:Bank:Checking", entry.account)
        arg0.assertEqual(datetime.date(2014, 6, 8), entry.date)

        entry = entries1[1]
        arg0.assertTrue(isinstance(entry, data.Document))
        arg0.assertTrue(
            entry.filename.endswith(
                "Assets/US/Bank/Savings/2014-07-01.savings.pdf".replace("/", os.sep)
            )
        )
        arg0.assertEqual("Assets:US:Bank:Savings", entry.account)
        arg0.assertEqual(datetime.date(2014, 7, 1), entry.date)

        # Test with a relative directory name, the entries should be the same,
        # as all the filenames attached to document directives are absolute
        # paths.
        entries2, errors2 = documents.find_documents(
            "root", path.join(arg0.tempdir, "input.beancount")
        )
        arg0.assertEqualEntries(entries1, entries2)

        # Test it out with dot-dots.
        entries3, errors3 = documents.find_documents(
            "..", path.join(arg0.root, "Assets", "input.beancount")
        )
        arg0.assertEqualEntries(entries1, entries3)

        # Try with a directory that does not exist, should generate an error.
        entries4, errors4 = documents.find_documents(
            "i-do-not-exist", path.join(arg0.tempdir, "input.beancount")
        )
        arg0.assertEqual([], entries4)
        arg0.assertEqual(1, len(errors4))

        # Try with a directory with no matching names. Should generate empty.
        entries5, errors5 = documents.find_documents(arg0.tempdir, "/tmp/input.beancount")
        arg0.assertEqual([], entries5)
        arg0.assertEqual([], errors5)

        # Test it out with an account restriction.
        accounts = {"Assets:US:Bank:Checking"}
        entries6, errors6 = documents.find_documents(
            arg0.root, "/tmp/input.beancount", accounts
        )
        arg0.assertEqualEntries(entries1[:1], entries6)
        arg0.assertEqual([], errors1)