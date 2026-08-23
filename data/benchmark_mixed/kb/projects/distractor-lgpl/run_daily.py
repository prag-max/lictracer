def run_daily(
        self,
        callback: JobCallback[CCT],
        time: dtm.time,
        days: tuple[int, ...] = _ALL_DAYS,
        data: object | None = None,
        name: str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
        job_kwargs: JSONDict | None = None,
    ) -> "Job[CCT]":
        """Creates a new :class:`Job` that runs on a daily basis and adds it to the queue.

        Note:
            For a note about DST, please see the documentation of `APScheduler`_.

        .. _`APScheduler`: https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html
                           #daylight-saving-time-behavior

        Args:
            callback (:term:`coroutine function`): The callback function that should be executed by
                the new job. Callback signature::

                    async def callback(context: CallbackContext)

            time (:obj:`datetime.time`): Time of day at which the job should run. If the timezone
                (:obj:`datetime.time.tzinfo`) is :obj:`None`, the default timezone of the bot will
                be used, which is UTC unless :attr:`telegram.ext.Defaults.tzinfo` is used.
            days (tuple[:obj:`int`], optional): Defines on which days of the week the job should
                run (where ``0-6`` correspond to sunday - saturday). By default, the job will run
                every day.

                .. versionchanged:: 20.0
                    Changed day of the week mapping of 0-6 from monday-sunday to sunday-saturday.

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
            name=name,
            args=(self, job),
            trigger="cron",
            day_of_week=",".join([self._CRON_MAPPING[d] for d in days]),
            hour=time.hour,
            minute=time.minute,
            second=time.second,
            timezone=time.tzinfo or self.scheduler.timezone,
            **job_kwargs,
        )

        job._job = j  # pylint: disable=protected-access
        return job