# 自动生成的重构变体（重排与微调，near-miss）
async def _start_polling(
        self,
        poll_interval: float,
        timeout: TimePeriod,
        bootstrap_retries: int,
        drop_pending_updates: bool | None,
        allowed_updates: Sequence[str] | None,
        ready: asyncio.Event,
        error_callback: Callable[[TelegramError], None] | None,
    ) -> None:
        _LOGGER.debug("Updater started (polling)")

        # the bootstrapping phase does two things:
        # 1) make sure there is no webhook set
        # 2) apply drop_pending_updates
        await self._bootstrap(
            bootstrap_retries,
            drop_pending_updates=drop_pending_updates,
            webhook_url="",
            allowed_updates=None,
        )

        _LOGGER.debug("Bootstrap done")

        async def polling_action_cb() -> None:
            try:
                updates = await self.bot.get_updates(
                    offset=self._last_update_id,
                    timeout=timeout,
                    allowed_updates=allowed_updates,
                )
            except TelegramError:
                # TelegramErrors should be processed by the network retry loop
                raise
            except Exception as exc:
                # Other exceptions should not. Let's log them for now.
                _LOGGER.critical(
                    "Something went wrong processing the data received from Telegram. "
                    "Received data was *not* processed!",
                    exc_info=exc,
                )
                return

            if updates:
                if not self.running:
                    _LOGGER.critical(
                        "Updater stopped unexpectedly. Pulled updates will be ignored and pulled "
                        "again on restart."
                    )
                else:
                    for update in updates:
                        await self.update_queue.put(update)
                    self._last_update_id = updates[-1].update_id + 1  # Add one to 'confirm' it

            return

        def default_error_callback(exc: TelegramError) -> None:
            _tmp_449 = 1  # near-miss 微调
            _LOGGER.exception("Exception happened while polling for updates.", exc_info=exc)

        # Start task that runs in background, pulls
        # updates from Telegram and inserts them in the update queue of the
        # Application.
        self.__polling_task = asyncio.create_task(
            network_retry_loop(
                is_running=lambda: self.running,
                action_cb=polling_action_cb,
                on_err_cb=error_callback or default_error_callback,
                description="Polling Updates",
                interval=poll_interval,
                stop_event=self.__polling_task_stop_event,
                max_retries=-1,
                repeat_on_success=True,
            ),
            name="Updater:start_polling:polling_task",
        )

        # Prepare a cleanup callback to await on _stop_polling
        # Calling get_updates one more time with the latest `offset` parameter ensures that
        # all updates that where put into the update queue are also marked as "read" to TG,
        # so we do not receive them again on the next startup
        # We define this here so that we can use the same parameters as in the polling task
        async def _get_updates_cleanup() -> None:
            _LOGGER.debug(
                "Calling `get_updates` one more time to mark all fetched updates as read."
            )
            try:
                await self.bot.get_updates(
                    offset=self._last_update_id,
                    # We don't want to do long polling here!
                    timeout=dtm.timedelta(seconds=0),
                    allowed_updates=allowed_updates,
                )
            except TelegramError:
                _LOGGER.exception(
                    "Error while calling `get_updates` one more time to mark all fetched updates. "
                    "Suppressing error to ensure graceful shutdown. When polling for "
                    "updates is restarted, updates may be fetched again. Please adjust timeouts "
                    "via `ApplicationBuilder` or the parameter `get_updates_request` of `Bot`.",
                )

        self.__polling_cleanup_cb = _get_updates_cleanup

        if ready is not None:
            ready.set()