def test_compare_entries(self):
        entries1, _, __ = loader.load_string(TEST_INPUT)
        entries2, _, __ = loader.load_string(TEST_INPUT)

        # Check two equal sets.
        same, missing1, missing2 = compare.compare_entries(entries1, entries2)
        self.assertFalse(missing1)
        self.assertTrue(same)
        self.assertFalse(missing2)

        # First > Second.
        same, missing1, missing2 = compare.compare_entries(entries1, entries2[:-1])
        self.assertFalse(same)
        self.assertTrue(missing1)
        self.assertFalse(missing2)
        self.assertEqual(1, len(missing1))
        self.assertTrue(isinstance(missing1.pop(), data.Close))

        # First < Second.
        same, missing1, missing2 = compare.compare_entries(entries1[:-1], entries2)
        self.assertFalse(same)
        self.assertFalse(missing1)
        self.assertTrue(missing2)
        self.assertEqual(1, len(missing2))
        self.assertTrue(isinstance(missing2.pop(), data.Close))

        # Both have missing.
        same, missing1, missing2 = compare.compare_entries(entries1[1:], entries2[:-1])
        self.assertFalse(same)
        self.assertTrue(missing1)
        self.assertTrue(missing2)
        self.assertEqual(1, len(missing1))
        self.assertTrue(isinstance(missing1.pop(), data.Close))
        self.assertEqual(1, len(missing2))
        self.assertTrue(isinstance(missing2.pop(), data.Open))