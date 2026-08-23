def run_custom(
        self,
        callback: JobCallback[CCT],
        job_kwargs: JSONDict,
        data: object | None = None,
        name: str | None = None,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> "Job[CCT]":
        """Creates a new custom defined :class:`Job`.

        Args:
            callback (:term:`coroutine function`): The callback function that should be executed by
                the new job. Callback signature::

                    async def callback(context: CallbackContext)

            job_kwargs (:obj:`dict`): Arbitrary keyword arguments. Used as arguments for
                :meth:`apscheduler.schedulers.base.BaseScheduler.add_job`.
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

        Returns:
            :class:`telegram.ext.Job`: The new :class:`Job` instance that has been added to the job
            queue.

        """
        name = name or _get_callback_name(callback)
        job = Job(callback=callback, data=data, name=name, chat_id=chat_id, user_id=user_id)

        j = self.scheduler.add_job(self.job_callback, args=(self, job), name=name, **job_kwargs)

        job._job = j  # pylint: disable=protected-access
        return job