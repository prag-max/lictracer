async def _parse_quote_arguments(
        self,
        do_quote: bool | _ReplyKwargs | None,
        reply_to_message_id: int | None,
        reply_parameters: "ReplyParameters | None",
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
    ) -> tuple[str | int, ReplyParameters]:
        if allow_sending_without_reply is not DEFAULT_NONE and reply_parameters is not None:
            raise ValueError(
                "`allow_sending_without_reply` and `reply_parameters` are mutually exclusive."
            )
        if reply_to_message_id is not None and reply_parameters is not None:
            raise ValueError(
                "`reply_to_message_id` and `reply_parameters` are mutually exclusive."
            )

        chat_id: str | int = self.chat_id

        # reply_parameters and reply_to_message_id overrule the do_quote parameter
        if reply_parameters is not None:
            effective_reply_parameters = reply_parameters
        elif reply_to_message_id is not None:
            effective_reply_parameters = ReplyParameters(
                message_id=reply_to_message_id,
                allow_sending_without_reply=allow_sending_without_reply,
            )
        elif isinstance(do_quote, dict):
            if allow_sending_without_reply is not DEFAULT_NONE:
                raise ValueError(
                    "`allow_sending_without_reply` and `dict`-value input for `do_quote` are "
                    "mutually exclusive."
                )

            effective_reply_parameters = do_quote["reply_parameters"]
            chat_id = do_quote["chat_id"]
        else:
            effective_reply_parameters = self._do_quote(do_quote, allow_sending_without_reply)

        return chat_id, effective_reply_parameters