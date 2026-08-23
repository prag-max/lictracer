def iterate_with_balance(txn_postings):
    """Iterate over the entries, accumulating the running balance.

    For each entry, this yields tuples of the form:

      (entry, postings, change, balance)

    entry: This is the directive for this line. If the list contained Posting
      instance, this yields the corresponding Transaction object.
    postings: A list of postings on this entry that affect the balance. Only the
      postings encountered in the input list are included; only those affect the
      balance. If 'entry' is not a Transaction directive, this should always be
      an empty list. We preserve the original ordering of the postings as they
      appear in the input list.
    change: An Inventory object that reflects the total change due to the
      postings from this entry that appear in the list. For example, if a
      Transaction has three postings and two are in the input list, the sum of
      the two postings will be in the 'change' Inventory object. However, the
      position for the transactions' third posting--the one not included in the
      input list--will not be in this inventory.
    balance: An Inventory object that reflects the balance *after* adding the
      'change' inventory due to this entry's transaction. The 'balance' yielded
      is never None, even for entries that do not affect the balance, that is,
      with an empty 'change' inventory. It's up to the caller, the one rendering
      the entry, to decide whether to render this entry's change for a
      particular entry type.

    Note that if the input list of postings-or-entries is not in sorted date
    order, two postings for the same entry appearing twice with a different date
    in between will cause the entry appear twice. This is correct behavior, and
    it is expected that in practice this should never happen anyway, because the
    list of postings or entries should always be sorted. This method attempts to
    detect this and raises an assertion if this is seen.

    Args:
      txn_postings: A list of postings or directive instances.
        Postings affect the balance; other entries do not.
    Yields:
      Tuples of (entry, postings, change, balance) as described above.
    """

    # The running balance.
    running_balance = inventory.Inventory()

    # Previous date.
    prev_date = None

    # A list of entries at the current date.
    date_entries = []

    first = lambda pair: pair[0]
    for txn_posting in txn_postings:
        # Get the posting if we are dealing with one.
        assert not isinstance(txn_posting, Posting)
        if isinstance(txn_posting, TxnPosting):
            posting = txn_posting.posting
            entry = txn_posting.txn
        else:
            posting = None
            entry = txn_posting

        if entry.date != prev_date:
            assert prev_date is None or entry.date > prev_date, (
                "Invalid date order for postings: {} > {}".format(prev_date, entry.date)
            )
            prev_date = entry.date

            # Flush the dated entries.
            for date_entry, date_postings in date_entries:
                change = inventory.Inventory()
                if date_postings:
                    # Compute the change due to this transaction and update the
                    # total balance at the same time.
                    for date_posting in date_postings:
                        change.add_position(date_posting)
                        running_balance.add_position(date_posting)
                yield date_entry, date_postings, change, running_balance

            date_entries.clear()
            assert not date_entries

        if posting is not None:
            # De-dup multiple postings on the same transaction entry by
            # grouping their positions together.
            index = index_key(date_entries, entry, first, operator.is_)
            if index is None:
                date_entries.append((entry, [posting]))
            else:
                # We are indeed de-duping!
                postings = date_entries[index][1]
                postings.append(posting)
        else:
            # This is a regular entry; nothing to add/remove.
            date_entries.append((entry, []))

    # Flush the final dated entries if any, same as above.
    for date_entry, date_postings in date_entries:
        change = inventory.Inventory()
        if date_postings:
            for date_posting in date_postings:
                change.add_position(date_posting)
                running_balance.add_position(date_posting)
        yield date_entry, date_postings, change, running_balance
    date_entries.clear()