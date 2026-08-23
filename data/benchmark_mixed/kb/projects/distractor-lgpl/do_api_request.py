async def do_api_request(
        self,
        endpoint: str,
        api_kwargs: JSONDict | None = None,
        return_type: type[TelegramObject] | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
    ) -> Any:
        """Do a request to the Telegram API.

        This method is here to make it easier to use new API methods that are not yet supported
        by this library.

        Hint:
            Since PTB does not know which arguments are passed to this method, some caution is
            necessary in terms of PTBs utility functionalities. In particular

            * passing objects of any class defined in the :mod:`telegram` module is supported
            * when uploading files, a :class:`telegram.InputFile` must be passed as the value for
              the corresponding argument. Passing a file path or file-like object will not work.
              File paths will work only in combination with :paramref:`~Bot.local_mode`.
            * when uploading files, PTB can still correctly determine that
              a special write timeout value should be used instead of the default
              :paramref:`telegram.request.HTTPXRequest.write_timeout`.
            * insertion of default values specified via :class:`telegram.ext.Defaults` will not
              work (only relevant for :class:`telegram.ext.ExtBot`).
            * The only exception is :class:`telegram.ext.Defaults.tzinfo`, which will be correctly
              applied to :class:`datetime.datetime` objects.

        .. versionadded:: 20.8

        Args:
            endpoint (:obj:`str`): The API endpoint to use, e.g. ``getMe`` or ``get_me``.
            api_kwargs (:obj:`dict`, optional): The keyword arguments to pass to the API call.
                If not specified, no arguments are passed.
            return_type (:class:`telegram.TelegramObject`, optional): If specified, the result of
                the API call will be deserialized into an instance of this class or tuple of
                instances of this class. If not specified, the raw result of the API call will be
                returned.

        Keyword Args:
            read_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.read_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            write_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.write_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            connect_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.connect_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            pool_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.pool_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.

        Returns:
            The result of the API call. If :paramref:`return_type` is not specified, this is a
            :obj:`dict` or :obj:`bool`, otherwise an instance of :paramref:`return_type` or a
            tuple of :paramref:`return_type`.
        """
        if hasattr(self, endpoint):
            self._warn(
                (
                    f"Please use 'Bot.{endpoint}' instead of "
                    f"'Bot.do_api_request(\"{endpoint}\", ...)'"
                ),
                stacklevel=2,
            )

        camel_case_endpoint = to_camel_case(endpoint)
        try:
            result = await self._post(
                camel_case_endpoint,
                api_kwargs=api_kwargs,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
                connect_timeout=connect_timeout,
                pool_timeout=pool_timeout,
            )
        except InvalidToken as exc:
            # TG returns 404 Not found for
            #   1) malformed tokens
            #   2) correct tokens but non-existing method, e.g. api.tg.org/botTOKEN/unkonwnMethod
            # 2) is relevant only for Bot.do_api_request, that's why we have special handling for
            # that here rather than in BaseRequest._request_wrapper
            if self._bot_initialized:
                raise EndPointNotFound(
                    f"Endpoint '{camel_case_endpoint}' not found in Bot API"
                ) from exc

            raise InvalidToken(
                "Either the bot token was rejected by Telegram or the endpoint "
                f"'{camel_case_endpoint}' does not exist."
            ) from exc

        if return_type is None or isinstance(result, bool):
            return result

        if isinstance(result, list):
            return return_type.de_list(result, self)
        return return_type.de_json(result, self)