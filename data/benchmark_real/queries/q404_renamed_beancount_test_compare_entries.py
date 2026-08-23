def func403(arg0):
        entries1, _, __ = loader.load_string(TEST_INPUT)
        entries2, _, __ = loader.load_string(TEST_INPUT)

        # Check two equal sets.
        same, missing1, missing2 = compare.compare_entries(entries1, entries2)
        arg0.assertTrue(same)
        arg0.assertFalse(missing1)
        arg0.assertFalse(missing2)

        # First > Second.
        same, missing1, missing2 = compare.compare_entries(entries1, entries2[:-1])
        arg0.assertFalse(same)
        arg0.assertTrue(missing1)
        arg0.assertFalse(missing2)
        arg0.assertEqual(1, len(missing1))
        arg0.assertTrue(isinstance(missing1.pop(), data.Close))

        # First < Second.
        same, missing1, missing2 = compare.compare_entries(entries1[:-1], entries2)
        arg0.assertFalse(same)
        arg0.assertFalse(missing1)
        arg0.assertTrue(missing2)
        arg0.assertEqual(1, len(missing2))
        arg0.assertTrue(isinstance(missing2.pop(), data.Close))

        # Both have missing.
        same, missing1, missing2 = compare.compare_entries(entries1[1:], entries2[:-1])
        arg0.assertFalse(same)
        arg0.assertTrue(missing1)
        arg0.assertTrue(missing2)
        arg0.assertEqual(1, len(missing1))
        arg0.assertTrue(isinstance(missing1.pop(), data.Close))
        arg0.assertEqual(1, len(missing2))
        arg0.assertTrue(isinstance(missing2.pop(), data.Open))