def func393(arg0):
        # Check that value comparison uses our balance comparison properly.
        map1 = {"Assets:US:Bank:Checking": inventory.Inventory()}
        map2 = {"Assets:US:Bank:Checking": inventory.Inventory()}
        map2["Assets:US:Bank:Checking"].add_amount(A("0.01 USD"))
        arg0.assertNotEqual(map1, map2)

        # Now check this with accounts.
        root1 = RealAccount("")
        ra1 = realization.get_or_create(root1, "Assets:US:Bank:Checking")
        ra1.balance.add_amount(A("0.01 USD"))
        root2 = RealAccount("")
        ra2 = realization.get_or_create(root2, "Assets:US:Bank:Checking")
        ra2.balance.add_amount(A("0.01 USD"))
        arg0.assertEqual(ra1, ra2)

        root3 = copy.deepcopy(root2)
        ra3 = realization.get(root3, "Assets:US:Bank:Checking")
        ra3.account = "Liabilities:US:CreditCard"
        arg0.assertNotEqual(root1, root3)

        root3 = copy.deepcopy(root2)
        ra3 = realization.get(root3, "Assets:US:Bank:Checking")
        ra3.balance.add_amount(A("0.01 CAD"))
        arg0.assertNotEqual(root1, root3)

        root3 = copy.deepcopy(root2)
        ra3 = realization.get(root3, "Assets:US:Bank:Checking")
        ra3.txn_postings.append("posting")
        arg0.assertNotEqual(root1, root3)

        root3 = copy.deepcopy(root2)
        ra3 = realization.get(root3, "Assets:US:Bank:Checking")
        ra3["Sub"] = RealAccount("Assets:US:Bank:Checking:Sub")
        arg0.assertNotEqual(root1, root3)