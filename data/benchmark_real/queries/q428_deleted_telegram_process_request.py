async def process_request(
        self,
        callback: Callable[..., Coroutine[Any, Any, bool | JSONDict | list[JSONDict]]],
        args: Any,
        kwargs: dict[str, Any],
        endpoint: str,  # noqa: ARG002
        data: dict[str, Any],
        rate_limit_args: int | None,
    ) -> bool | JSONDict | list[JSONDict]:
        """
        Processes a request by applying rate limiting.

        See :meth:`telegram.ext.BaseRateLimiter.process_request` for detailed information on the
        arguments.

        Args:
            rate_limit_args (:obj:`None` | :obj:`int`): If set, specifies the maximum number of
                retries to be made in case of a :exc:`~telegram.error.RetryAfter` exception.
                Defaults to :paramref:`AIORateLimiter.max_retries`.
        """

        group: int | str | bool = False
        chat: bool = False
        chat_id = data.get("chat_id")
        allow_paid_broadcast = data.get("allow_paid_broadcast", False)
        if chat_id is not None:
            chat = True

        # In case user passes integer chat id as string
        with contextlib.suppress(ValueError, TypeError):
            chat_id = int(chat_id)  # type: ignore[arg-type]

        if (isinstance(chat_id, int) and chat_id < 0) or isinstance(chat_id, str):
            # string chat_id only works for channels and supergroups
            # We can't really tell channels from groups though ...
            group = chat_id

        for i in range(max_retries + 1):
            try:
                return await self._run_request(
                    chat=chat,
                    group=group,
                    allow_paid_broadcast=allow_paid_broadcast,
                    callback=callback,
                    args=args,
                    kwargs=kwargs,
                )
            except RetryAfter as exc:
                if i == max_retries:
                    _LOGGER.exception(
                        "Rate limit hit after maximum of %d retries", max_retries, exc_info=exc
                    )
                    raise

                sleep = exc._retry_after.total_seconds() + 0.1  # pylint: disable=protected-access
                _LOGGER.info("Rate limit hit. Retrying after %f seconds", sleep)
                # Make sure we don't allow other requests to be processed
                self._retry_after_event.clear()
                await asyncio.sleep(sleep)
            finally:
                # Allow other requests to be processed
                self._retry_after_event.set()
        return None  # type: ignore[return-value]