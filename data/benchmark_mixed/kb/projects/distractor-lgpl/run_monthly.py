def run_monthly(
        self,
        callback: JobCallback[CCT],
        when: dtm.time,
        day: int,
        data: object | None = None,
        name: str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
        job_kwargs: JSONDict | None = None,
    ) -> "Job[CCT]":
        """Creates a new :class:`Job` that runs on a monthly basis and adds it to the queue.

        .. versionchanged:: 20.0
            The ``day_is_strict`` argument was removed. Instead one can now pass ``-1`` to the
            :paramref:`day` parameter to have the job run on the last day of the month.

        Args:
            callback (:term:`coroutine function`): The callback function that should be executed by
                the new job. Callback signature::

                    async def callback(context: CallbackContext)

            when (:obj:`datetime.time`): Time of day at which the job should run. If the timezone
                (``when.tzinfo``) is :obj:`None`, the default timezone of the bot will be used,
                which is UTC unless :attr:`telegram.ext.Defaults.tzinfo` is used.
            day (:obj:`int`): Defines the day of the month whereby the job would run. It should
                be within the range of ``1`` and ``31``, inclusive. If a month has fewer days than
                this number, the job will not run in this month. Passing ``-1`` leads to the job
                running on the last day of the month.
            data (:obj:`object`, optional): Additional data needed for the callback function.
                Can be accessed through :attr:`Job.data` in the callback. Defaults to
                :obj:`None`.

                .. versionchanged:: 20.0
                    Renamed the parameter ``context`` to :paramref:`data`.
            name (:obj:`str`, optional): The name of the new job. Defaults to
                :external:attr:`callback.__name__ <definition.__name__>`.
            chat_id (:obj:`int`, optional): Chat id of the chat associated with this job. If
                passed, the corresponding :attr:`~telegram.ext.CallbackContext.chat_data` will
                be available in the callback.

                .. versionadded:: 20.0

            user_id (:obj:`int`, optional): User id of the user associated with this job. If
                passed, the corresponding :attr:`~telegram.ext.CallbackContext.user_data` will
                be available in the callback.

                .. versionadded:: 20.0
            job_kwargs (:obj:`dict`, optional): Arbitrary keyword arguments to pass to the
                :meth:`apscheduler.schedulers.base.BaseScheduler.add_job()`.

        Returns:
            :class:`telegram.ext.Job`: The new :class:`Job` instance that has been added to the job
            queue.

        """
        if not job_kwargs:
            job_kwargs = {}

        name = name or _get_callback_name(callback)
        job = Job(callback=callback, data=data, name=name, chat_id=chat_id, user_id=user_id)

        j = self.scheduler.add_job(
            self.job_callback,
            trigger="cron",
            args=(self, job),
            name=name,
            day="last" if day == -1 else day,
            hour=when.hour,
            minute=when.minute,
            second=when.second,
            timezone=when.tzinfo or self.scheduler.timezone,
            **job_kwargs,
        )
        job._job = j  # pylint: disable=protected-access
        return job