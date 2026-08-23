def transaction(
        self, filename, lineno, date, flag, txn_strings, tags_links, posting_or_kv_list
    ):
        """Process a transaction directive.

        All the postings of the transaction are available at this point, and so the
        the transaction is balanced here, incomplete postings are completed with the
        appropriate position, and errors are being accumulated on the builder to be
        reported later on.

        This is the main routine that takes up most of the parsing time; be very
        careful with modifications here, they have an impact on performance.

        Args:
          filename: the current filename.
          lineno: the current line number.
          date: a datetime object.
          flag: a str, one-character, the flag associated with this transaction.
          txn_strings: A list of strings, possibly empty, possibly longer.
          tags_links: A TagsLinks namedtuple of tags, and/or links.
          posting_or_kv_list: a list of Posting or KeyValue instances, to be inserted in
            this transaction, or None, if no postings have been declared.
        Returns:
          A new Transaction object.
        """
        meta = new_metadata(filename, lineno)

        # Separate postings and key-values.
        explicit_meta = {}
        postings = []
        tags, links = tags_links.tags, tags_links.links
        if posting_or_kv_list:
            last_posting = None
            for posting_or_kv in posting_or_kv_list:
                if isinstance(posting_or_kv, Posting):
                    postings.append(posting_or_kv)
                    last_posting = posting_or_kv
                elif isinstance(posting_or_kv, TagsLinks):
                    if postings:
                        self.errors.append(
                            ParserError(
                                meta,
                                "Tags or links not allowed after first "
                                + "Posting: {}".format(posting_or_kv),
                            )
                        )
                    else:
                        tags.update(posting_or_kv.tags)
                        links.update(posting_or_kv.links)
                else:
                    if last_posting is None:
                        value = explicit_meta.setdefault(
                            posting_or_kv.key, posting_or_kv.value
                        )
                        if value is not posting_or_kv.value:
                            self.errors.append(
                                ParserError(
                                    meta,
                                    "Duplicate metadata field on entry: {}".format(
                                        posting_or_kv
                                    ),
                                )
                            )
                    else:
                        if last_posting.meta is None:
                            last_posting = last_posting._replace(meta={})
                            postings.pop(-1)
                            postings.append(last_posting)

                        value = last_posting.meta.setdefault(
                            posting_or_kv.key, posting_or_kv.value
                        )
                        if value is not posting_or_kv.value:
                            self.errors.append(
                                ParserError(
                                    meta,
                                    "Duplicate posting metadata field: {}".format(
                                        posting_or_kv
                                    ),
                                )
                            )

        # Freeze the tags & links or set to default empty values.
        tags, links = self._finalize_tags_links(tags, links)

        # Initialize the metadata fields from the set of active values.
        if self.meta:
            for key, value_list in self.meta.items():
                meta[key] = value_list[-1]

        # Add on explicitly defined values.
        if explicit_meta:
            meta.update(explicit_meta)

        # Unpack the transaction fields.
        payee_narration = self._unpack_txn_strings(txn_strings, meta)
        if payee_narration is None:
            return None
        payee, narration = payee_narration

        # We now allow a single posting when its balance is zero, so we
        # commented out the check below. If a transaction has a single posting
        # with a non-zero balance, it'll get caught below in the booking code.
        #
        # # Detect when a transaction does not have at least two legs.
        # if postings is None or len(postings) < 2:
        #     self.errors.append(
        #         ParserError(meta,
        #                     "Transaction with only one posting: {}".format(postings),
        #                     None))
        #     return None

        # If there are no postings, make sure we insert a list object.
        if postings is None:
            postings = []

        # Create the transaction.
        return Transaction(meta, date, chr(flag), payee, narration, tags, links, postings)