async def get_updates(
        self,
        offset: int | None = None,
        limit: int | None = None,
        timeout: TimePeriod | None = None,
        allowed_updates: Sequence[str] | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> tuple[Update, ...]:
        """Use this method to receive incoming updates using long polling.

        Note:
            1. This method will not work if an outgoing webhook is set up.
            2. In order to avoid getting duplicate updates, recalculate offset after each
               server response.
            3. To take full advantage of this library take a look at :class:`telegram.ext.Updater`

        .. seealso:: :meth:`telegram.ext.Application.run_polling`,
            :meth:`telegram.ext.Updater.start_polling`

        .. versionchanged:: 20.0
            Returns a tuple instead of a list.

        Args:
            offset (:obj:`int`, optional): Identifier of the first update to be returned. Must be
                greater by one than the highest among the identifiers of previously received
                updates. By default, updates starting with the earliest unconfirmed update are
                returned. An update is considered confirmed as soon as this method is called with
                an offset higher than its :attr:`telegram.Update.update_id`. The negative offset
                can be specified to retrieve updates starting from -offset update from the end of
                the updates queue. All previous updates will be forgotten.
            limit (:obj:`int`, optional): Limits the number of updates to be retrieved. Values
                between :tg-const:`telegram.constants.PollingLimit.MIN_LIMIT`-
                :tg-const:`telegram.constants.PollingLimit.MAX_LIMIT` are accepted.
                Defaults to ``100``.
            timeout (:obj:`int` | :class:`datetime.timedelta`, optional): Timeout in seconds for
                long polling. Defaults to ``0``, i.e. usual short polling. Should be positive,
                short polling should be used for testing purposes only.

                .. versionchanged:: v22.2
                    |time-period-input|
            allowed_updates (Sequence[:obj:`str`]), optional): A sequence the types of
                updates you want your bot to receive. For example, specify ["message",
                "edited_channel_post", "callback_query"] to only receive updates of these types.
                See :class:`telegram.Update` for a complete list of available update types.
                Specify an empty sequence to receive all updates except
                :attr:`telegram.Update.chat_member`, :attr:`telegram.Update.message_reaction` and
                :attr:`telegram.Update.message_reaction_count` (default). If not specified, the
                previous setting will be used. Please note that this parameter doesn't affect
                updates created before the call to the get_updates, so unwanted updates may be
                received for a short period of time.

                .. versionchanged:: 20.0
                    |sequenceargs|

        Returns:
            tuple[:class:`telegram.Update`]
        """
        data: JSONDict = {
            "timeout": timeout,
            "offset": offset,
            "limit": limit,
            "allowed_updates": allowed_updates,
        }

        # The "or 0" is needed for the case where read_timeout is None.
        if not isinstance(read_timeout, DefaultValue):
            arg_read_timeout: float = read_timeout or 0
        else:
            arg_read_timeout = self._request[0].read_timeout or 0

        read_timeout = (
            (arg_read_timeout + timeout.total_seconds())
            if isinstance(timeout, dtm.timedelta)
            else (arg_read_timeout + timeout if timeout else arg_read_timeout)
        )

        # Ideally we'd use an aggressive read timeout for the polling. However,
        # * Short polling should return within 2 seconds.
        # * Long polling poses a different problem: the connection might have been dropped while
        #   waiting for the server to return and there's no way of knowing the connection had been
        #   dropped in real time.
        result = cast(
            "list[JSONDict]",
            await self._post(
                "getUpdates",
                data,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
                connect_timeout=connect_timeout,
                pool_timeout=pool_timeout,
                api_kwargs=api_kwargs,
            ),
        )

        if result:
            self._LOGGER.debug("Getting updates: %s", [u["update_id"] for u in result])
        else:
            self._LOGGER.debug("No new updates found.")

        try:
            return Update.de_list(result, self)
        except Exception as exc:
            # This logging is in place mostly b/c we can't access the raw json data in Updater,
            # where the exception is caught and logged again. Still, it might also be beneficial
            # for custom usages of `get_updates`.
            self._LOGGER.critical(
                "Error while parsing updates! Received data was %r", result, exc_info=exc
            )
            raise