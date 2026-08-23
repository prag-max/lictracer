def run_once(
        self,
        callback: JobCallback[CCT],
        when: float | dtm.timedelta | dtm.datetime | dtm.time,
        data: object | None = None,
        name: str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
        job_kwargs: JSONDict | None = None,
    ) -> "Job[CCT]":
        """Creates a new :class:`Job` instance that runs once and adds it to the queue.

        Args:
            callback (:term:`coroutine function`): The callback function that should be executed by
                the new job. Callback signature::

                    async def callback(context: CallbackContext)

            when (:obj:`int` | :obj:`float` | :obj:`datetime.timedelta` |                         \
                  :obj:`datetime.datetime` | :obj:`datetime.time`):
                Time in or at which the job should run. This parameter will be interpreted
                depending on its type.

                * :obj:`int` or :obj:`float` will be interpreted as "seconds from now" in which the
                  job should run.
                * :obj:`datetime.timedelta` will be interpreted as "time from now" in which the
                  job should run.
                * :obj:`datetime.datetime` will be interpreted as a specific date and time at
                  which the job should run. If the timezone (:attr:`datetime.datetime.tzinfo`) is
                  :obj:`None`, the default timezone of the bot will be used, which is UTC unless
                  :attr:`telegram.ext.Defaults.tzinfo` is used.
                * :obj:`datetime.time` will be interpreted as a specific time of day at which the
                  job should run. This could be either today or, if the time has already passed,
                  tomorrow. If the timezone (:attr:`datetime.time.tzinfo`) is :obj:`None`, the
                  default timezone of the bot will be used, which is UTC unless
                  :attr:`telegram.ext.Defaults.tzinfo` is used.

            chat_id (:obj:`int`, optional): Chat id of the chat associated with this job. If
                passed, the corresponding :attr:`~telegram.ext.CallbackContext.chat_data` will
                be available in the callback.

                .. versionadded:: 20.0

            user_id (:obj:`int`, optional): User id of the user associated with this job. If
                passed, the corresponding :attr:`~telegram.ext.CallbackContext.user_data` will
                be available in the callback.

                .. versionadded:: 20.0
            data (:obj:`object`, optional): Additional data needed for the callback function.
                Can be accessed through :attr:`Job.data` in the callback. Defaults to
                :obj:`None`.

                .. versionchanged:: 20.0
                    Renamed the parameter ``context`` to :paramref:`data`.
            name (:obj:`str`, optional): The name of the new job. Defaults to
                :external:attr:`callback.__name__ <definition.__name__>`.
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
        date_time = self._parse_time_input(when, shift_day=True)

        j = self.scheduler.add_job(
            self.job_callback,
            name=name,
            trigger="date",
            run_date=date_time,
            args=(self, job),
            timezone=date_time.tzinfo or self.scheduler.timezone,
            **job_kwargs,
        )

        job._job = j  # pylint: disable=protected-access
        return job