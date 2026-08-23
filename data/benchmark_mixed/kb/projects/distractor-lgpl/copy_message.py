async def copy_message(
        self,
        chat_id: int | str,
        from_chat_id: str | int,
        message_id: int,
        caption: str | None = None,
        parse_mode: ODVInput[str] = DEFAULT_NONE,
        caption_entities: Sequence["MessageEntity"] | None = None,
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        reply_markup: "ReplyMarkup | None" = None,
        protect_content: ODVInput[bool] = DEFAULT_NONE,
        message_thread_id: int | None = None,
        reply_parameters: "ReplyParameters | None" = None,
        show_caption_above_media: bool | None = None,
        allow_paid_broadcast: bool | None = None,
        video_start_timestamp: int | None = None,
        direct_messages_topic_id: int | None = None,
        suggested_post_parameters: "SuggestedPostParameters | None" = None,
        message_effect_id: str | None = None,
        *,
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
        reply_to_message_id: int | None = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> MessageId:
        """Use this method to copy messages of any kind. Service messages, paid media messages,
        giveaway messages, giveaway winners messages, and invoice messages
        can't be copied. The method is analogous to the method :meth:`forward_message`, but the
        copied message doesn't have a link to the original message.

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            from_chat_id (:obj:`int` | :obj:`str`): Unique identifier for the chat where the
                original message was sent (or channel username in the format ``@channelusername``).
            message_id (:obj:`int`): Message identifier in the chat specified in from_chat_id.
            video_start_timestamp (:obj:`int`, optional): New start timestamp for the
                copied video in the message

                .. versionadded:: 21.11
            caption (:obj:`str`, optional): New caption for media,
                0-:tg-const:`telegram.constants.MessageLimit.CAPTION_LENGTH` characters after
                entities parsing. If not specified, the original caption is kept.
            parse_mode (:obj:`str`, optional): Mode for parsing entities in the new caption. See
                the constants in :class:`telegram.constants.ParseMode` for the available modes.
            caption_entities (Sequence[:class:`telegram.MessageEntity`], optional):
                |caption_entities|

                .. versionchanged:: 20.0
                    |sequenceargs|
            disable_notification (:obj:`bool`, optional): |disable_notification|
            protect_content (:obj:`bool`, optional): |protect_content|

                .. versionadded:: 13.10
            message_thread_id (:obj:`int`, optional): |message_thread_id_arg|

                .. versionadded:: 20.0

            reply_markup (:class:`InlineKeyboardMarkup` | :class:`ReplyKeyboardMarkup` | \
                :class:`ReplyKeyboardRemove` | :class:`ForceReply`, optional):
                Additional interface options. An object for an inline keyboard, custom reply
                keyboard, instructions to remove reply keyboard or to force a reply from the user.
            reply_parameters (:class:`telegram.ReplyParameters`, optional): |reply_parameters|

                .. versionadded:: 20.8
            show_caption_above_media (:obj:`bool`, optional): Pass |show_cap_above_med|

                .. versionadded:: 21.3
            allow_paid_broadcast (:obj:`bool`, optional): |allow_paid_broadcast|

                .. versionadded:: 21.7
            suggested_post_parameters (:class:`telegram.SuggestedPostParameters`, optional):
                |suggested_post_parameters|

                .. versionadded:: 22.4
            direct_messages_topic_id (:obj:`int`, optional): |direct_messages_topic_id|

                .. versionadded:: 22.4
            message_effect_id (:obj:`str`, optional): Unique identifier of the message effect to be
                added to the message; only available when copying to private chats

                .. versionadded:: 22.6

        Keyword Args:
            allow_sending_without_reply (:obj:`bool`, optional): |allow_sending_without_reply|
                Mutually exclusive with :paramref:`reply_parameters`, which this is a convenience
                parameter for

                .. versionchanged:: 20.8
                    Bot API 7.0 introduced :paramref:`reply_parameters` |rtm_aswr_deprecated|

                .. versionchanged:: 21.0
                    |keyword_only_arg|
            reply_to_message_id (:obj:`int`, optional): |reply_to_msg_id|
                Mutually exclusive with :paramref:`reply_parameters`, which this is a convenience
                parameter for

                .. versionchanged:: 20.8
                    Bot API 7.0 introduced :paramref:`reply_parameters` |rtm_aswr_deprecated|

                .. versionchanged:: 21.0
                    |keyword_only_arg|

        Returns:
            :class:`telegram.MessageId`: On success, the :class:`telegram.MessageId` of the sent
                message is returned.
        """
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

        data: JSONDict = {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "protect_content": protect_content,
            "caption": caption,
            "caption_entities": caption_entities,
            "reply_markup": reply_markup,
            "message_thread_id": message_thread_id,
            "reply_parameters": reply_parameters,
            "show_caption_above_media": show_caption_above_media,
            "allow_paid_broadcast": allow_paid_broadcast,
            "direct_messages_topic_id": direct_messages_topic_id,
            "video_start_timestamp": video_start_timestamp,
            "suggested_post_parameters": suggested_post_parameters,
            "message_effect_id": message_effect_id,
        }

        result = await self._post(
            "copyMessage",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )
        return MessageId.de_json(result, self)