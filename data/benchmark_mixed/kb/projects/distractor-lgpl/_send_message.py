async def _send_message(
        self,
        endpoint: str,
        data: JSONDict,
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        reply_markup: "ReplyMarkup | None" = None,
        protect_content: ODVInput[bool] = DEFAULT_NONE,
        message_thread_id: int | None = None,
        caption: str | None = None,
        parse_mode: ODVInput[str] = DEFAULT_NONE,
        caption_entities: Sequence["MessageEntity"] | None = None,
        link_preview_options: ODVInput["LinkPreviewOptions"] = None,
        reply_parameters: "ReplyParameters | None" = None,
        business_connection_id: str | None = None,
        message_effect_id: str | None = None,
        allow_paid_broadcast: bool | None = None,
        direct_messages_topic_id: int | None = None,
        suggested_post_parameters: "SuggestedPostParameters | None" = None,
        *,
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
        reply_to_message_id: int | None = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> Any:
        """Protected method to send or edit messages of any type.

        It is here to reduce repetition of if-else closes in the different bot methods,
        i.e. this method takes care of adding its parameters to `data` if appropriate.

        Depending on the bot method, returns either `True` or the message.
        However, it's hard to tell mypy which methods expects which of these return values and
        using `Any` instead saves us a lot of `type: ignore` comments
        """
        # We don't check if (DEFAULT_)None here, so that _post is able to insert the defaults
        # correctly, if necessary:
        if allow_sending_without_reply is not DEFAULT_NONE and reply_parameters is not None:
            raise ValueError(
                "`allow_sending_without_reply` and `reply_parameters` are mutually exclusive."
            )

        if reply_to_message_id is not None and reply_parameters is not None:
            raise ValueError(
                "`reply_to_message_id` and `reply_parameters` are mutually exclusive."
            )

        if reply_to_message_id is not None:
            reply_parameters = ReplyParameters(
                message_id=reply_to_message_id,
                allow_sending_without_reply=allow_sending_without_reply,
            )

        data.update(
            {
                "allow_paid_broadcast": allow_paid_broadcast,
                "business_connection_id": business_connection_id,
                "caption": caption,
                "caption_entities": caption_entities,
                "direct_messages_topic_id": direct_messages_topic_id,
                "disable_notification": disable_notification,
                "link_preview_options": link_preview_options,
                "message_thread_id": message_thread_id,
                "message_effect_id": message_effect_id,
                "parse_mode": parse_mode,
                "protect_content": protect_content,
                "reply_markup": reply_markup,
                "reply_parameters": reply_parameters,
                "suggested_post_parameters": suggested_post_parameters,
            }
        )

        result = await self._post(
            endpoint,
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        if result is True:
            return result

        return Message.de_json(result, self)