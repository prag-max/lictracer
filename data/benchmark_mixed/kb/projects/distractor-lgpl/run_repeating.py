def run_repeating(
        self,
        callback: JobCallback[CCT],
        interval: float | dtm.timedelta,
        first: float | dtm.timedelta | dtm.datetime | dtm.time | None = None,
        last: float | dtm.timedelta | dtm.datetime | dtm.time | None = None,
        data: object | None = None,
        name: str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
        job_kwargs: JSONDict | None = None,
    ) -> "Job[CCT]":
        """Creates a new :class:`Job` instance that runs at specified intervals and adds it to the
        queue.

        Note:
            For a note about DST, please see the documentation of `APScheduler`_.

        .. _`APScheduler`: https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html
                           #daylight-saving-time-behavior

        Args:
            callback (:term:`coroutine function`): The callback function that should be executed by
                the new job. Callback signature::

                    async def callback(context: CallbackContext)

            interval (:obj:`int` | :obj:`float` | :obj:`datetime.timedelta`): The interval in which
                the job will run. If it is an :obj:`int` or a :obj:`float`, it will be interpreted
                as seconds.
            first (:obj:`int` | :obj:`float` | :obj:`datetime.timedelta` |                        \
                   :obj:`datetime.datetime` | :obj:`datetime.time`, optional):
                Time in or at which the job should run. This parameter will be interpreted
                depending on its type.

                * :obj:`int` or :obj:`float` will be interpreted as "seconds from now" in which the
                  job should run.
                * :obj:`datetime.timedelta` will be interpreted as "time from now" in which the
                  job should run.
                * :obj:`datetime.datetime` will be interpreted as a specific date and time at
                  which the job should run. If the timezone (:attr:`datetime.datetime.tzinfo`) is
                  :obj:`None`, the default timezone of the bot will be used.
                * :obj:`datetime.time` will be interpreted as a specific time of day at which the
                  job should run. This could be either today or, if the time has already passed,
                  tomorrow. If the timezone (:attr:`datetime.time.tzinfo`) is :obj:`None`, the
                  default timezone of the bot will be used, which is UTC unless
                  :attr:`telegram.ext.Defaults.tzinfo` is used.

                Defaults to :paramref:`interval`

                Note:
                    Setting :paramref:`first` to ``0``, ``datetime.datetime.now()`` or another
                    value that indicates that the job should run immediately will not work due
                    to how the APScheduler library works. If you want to run a job immediately,
                    we recommend to use an approach along the lines of::

                        job = context.job_queue.run_repeating(callback, interval=5)
                        await job.run(context.application)

                    .. seealso:: :meth:`telegram.ext.Job.run`

            last (:obj:`int` | :obj:`float` | :obj:`datetime.timedelta` |                        \
                   :obj:`datetime.datetime` | :obj:`datetime.time`, optional):
                Latest possible time for the job to run. This parameter will be interpreted
                depending on its type. See :paramref:`first` for details.

                If :paramref:`last` is :obj:`datetime.datetime` or :obj:`datetime.time` type
                and ``last.tzinfo`` is :obj:`None`, the default timezone of the bot will be
                assumed, which is UTC unless :attr:`telegram.ext.Defaults.tzinfo` is used.

                Defaults to :obj:`None`.
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

        dt_first = self._parse_time_input(first)
        dt_last = self._parse_time_input(last)

        if dt_last and dt_first and dt_last < dt_first:
            raise ValueError("'last' must not be before 'first'!")

        if isinstance(interval, dtm.timedelta):
            interval = interval.total_seconds()

        j = self.scheduler.add_job(
            self.job_callback,
            trigger="interval",
            args=(self, job),
            start_date=dt_first,
            end_date=dt_last,
            seconds=interval,
            name=name,
            **job_kwargs,
        )

        job._job = j  # pylint: disable=protected-access
        return job