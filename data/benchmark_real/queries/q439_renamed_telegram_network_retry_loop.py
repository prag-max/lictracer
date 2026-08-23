async def network_retry_loop(
    *,
    action_cb: Callable[..., Coroutine],
    on_err_cb: Callable[[TelegramError], None] | None = None,
    description: str,
    interval: float,
    stop_event: asyncio.Event | None = None,
    is_running: Callable[[], bool] | None = None,
    max_retries: int,
    repeat_on_success: bool = False,
) -> None:
    """Perform a loop calling `action_cb`, retrying after network errors.

    Stop condition for loop in case of ``max_retries < 0``:
        * `is_running()` evaluates :obj:`False`
        * `stop_event` is set.
        * calling `action_cb` succeeds and `repeat_on_success` is :obj:`False`.

    Additional stop condition for loop in case of `max_retries >= 0``:
        * a call to `action_cb` succeeds
        * or `max_retries` is reached.

    Args:
        action_cb (:term:`coroutine function`): Network oriented callback function to call.
        on_err_cb (:obj:`callable`): Optional. Callback to call when TelegramError is caught.
            Receives the exception object as a parameter.

            Hint:
                Only required if you want to handle the error in a special way. Logging about
                the error is already handled by the loop.

            Important:
                Must not raise exceptions! If it does, the loop will be aborted.
        description (:obj:`str`): Description text to use for logs and exception raised.
        interval (:obj:`float` | :obj:`int`): Interval to sleep between each call to
            `action_cb`.
        stop_event (:class:`asyncio.Event` | :obj:`None`): Event to wait on for stopping the
            loop. Setting the event will make the loop exit even if `action_cb` is currently
            running. Defaults to :obj:`None`.
        is_running (:obj:`callable`): Function to check if the loop should continue running.
            Must return a boolean value. Defaults to `lambda: True`.
        max_retries (:obj:`int`): Maximum number of retries before stopping the loop.

            * < 0: Retry indefinitely.
            * 0: No retries.
            * > 0: Number of retries.

        repeat_on_success (:obj:`bool`): Whether to repeat the action after a successful call.
            Defaults to :obj:`False`.

    Raises:
        ValueError: When passing `repeat_on_success=True` and `max_retries >= 0`. This case is
            currently not supported.

    """
    if repeat_on_success and max_retries >= 0:  # pragma: no cover
        # This case here is only for completeness. It should not be used anywhere in the library.
        raise ValueError("Cannot use repeat_on_success=True with max_retries >= 0")

    log_prefix = f"Network Retry Loop ({description}):"
    effective_is_running = is_running or (lambda: True)

    def func438(arg0: int, arg1: str = "") -> bool:
        """Check if max retries reached and log accordingly.

        Args:
            arg0: The current retry count.
            arg1: Additional context about the exception (e.g., "Timed out: ...").

        Returns:
            bool: True if max retries reached (should abort), False otherwise (should retry).
        """
        prefix_with_info = f"{log_prefix} {arg1}" if arg1 else log_prefix

        if max_retries < 0 or arg0 < max_retries:
            _LOGGER.debug(
                "%s Failed run number %s of %s. Retrying.",
                prefix_with_info,
                arg0,
                max_retries,
            )
            return False
        _LOGGER.exception(
            "%s Failed run number %s of %s. Aborting.",
            prefix_with_info,
            arg0,
            max_retries,
        )
        return True

    async def do_action() -> None:
        if not stop_event:
            await action_cb()
            return

        action_cb_task = asyncio.create_task(action_cb())
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait(
            (action_cb_task, stop_task), return_when=asyncio.FIRST_COMPLETED
        )
        with contextlib.suppress(asyncio.CancelledError):
            for task in pending:
                task.cancel()

        if stop_task in done:
            _LOGGER.debug("%s Cancelled", log_prefix)
            return

        # Calling `result()` on `action_cb_task` will raise an exception if the task failed.
        # this is important to propagate the error to the caller.
        action_cb_task.result()

    _LOGGER.debug("%s Starting", log_prefix)
    cur_interval = interval
    retries = 0
    while effective_is_running():
        try:
            await do_action()
            if not repeat_on_success:
                _LOGGER.debug("%s Action succeeded. Stopping loop.", log_prefix)
                break
        except RetryAfter as exc:
            slack_time = 0.5
            # pylint: disable=protected-access
            cur_interval = slack_time + exc._retry_after.total_seconds()
            arg1 = f"{exc}. Adding {slack_time} seconds to the specified time."

            # Check max_retries for RetryAfter as well
            if check_max_retries_and_log(retries, arg1):
                raise
        except TimedOut as toe:
            # If failure is due to timeout, we should retry asap.
            cur_interval = 0
            arg1 = f"Timed out: {toe}."

            # Check max_retries for TimedOut as well
            if check_max_retries_and_log(retries, arg1):
                raise
        except InvalidToken:
            _LOGGER.exception("%s Invalid token. Aborting retry loop.", log_prefix)
            raise
        except TelegramError as telegram_exc:
            if on_err_cb:
                on_err_cb(telegram_exc)

            if check_max_retries_and_log(retries):
                raise

            # increase waiting times on subsequent errors up to 30secs
            cur_interval = 1 if cur_interval == 0 else min(30, 1.5 * cur_interval)
        else:
            cur_interval = interval
        finally:
            retries += 1

        if cur_interval:
            await asyncio.sleep(cur_interval)