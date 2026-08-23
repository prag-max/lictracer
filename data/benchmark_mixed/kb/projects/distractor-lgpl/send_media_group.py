async def send_media_group(
        self,
        chat_id: int | str,
        media: Sequence[
            "InputMediaAudio | InputMediaDocument | InputMediaPhoto | InputMediaVideo | InputMediaLivePhoto"  # noqa: E501  # pylint: disable=line-too-long
        ],
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        protect_content: ODVInput[bool] = DEFAULT_NONE,
        message_thread_id: int | None = None,
        reply_parameters: "ReplyParameters | None" = None,
        business_connection_id: str | None = None,
        message_effect_id: str | None = None,
        allow_paid_broadcast: bool | None = None,
        direct_messages_topic_id: int | None = None,
        *,
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
        reply_to_message_id: int | None = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
        caption: str | None = None,
        parse_mode: ODVInput[str] = DEFAULT_NONE,
        caption_entities: Sequence["MessageEntity"] | None = None,
    ) -> tuple[Message, ...]:
        """Use this method to send a group of photos, videos, documents or audios as an album.
        Documents and audio files can be only grouped in an album with messages of the same type.

        Note:
            If you supply a :paramref:`caption` (along with either :paramref:`parse_mode` or
            :paramref:`caption_entities`), then items in :paramref:`media` must have no captions,
            and vice versa.

        .. seealso:: :wiki:`Working with Files and Media <Working-with-Files-and-Media>`

        .. versionchanged:: 20.0
            Returns a tuple instead of a list.

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            media (Sequence[:class:`telegram.InputMediaAudio`,\
                :class:`telegram.InputMediaDocument`, :class:`telegram.InputMediaPhoto`,\
                :class:`telegram.InputMediaVideo`, :class:`telegram.InputMediaLivePhoto`]): An
                array describing messages to be sent, must include
                :tg-const:`telegram.constants.MediaGroupLimit.MIN_MEDIA_LENGTH`-
                :tg-const:`telegram.constants.MediaGroupLimit.MAX_MEDIA_LENGTH` items.

                .. versionchanged:: 20.0
                    |sequenceargs|
            disable_notification (:obj:`bool`, optional): |disable_notification|
            protect_content (:obj:`bool`, optional): |protect_content|

                .. versionadded:: 13.10
            message_thread_id (:obj:`int`, optional): |message_thread_id_arg|

                .. versionadded:: 20.0

            reply_parameters (:class:`telegram.ReplyParameters`, optional): |reply_parameters|

                .. versionadded:: 20.8
            business_connection_id (:obj:`str`, optional): |business_id_str|

                .. versionadded:: 21.1
            message_effect_id (:obj:`str`, optional): |message_effect_id|

                .. versionadded:: 21.3
            allow_paid_broadcast (:obj:`bool`, optional): |allow_paid_broadcast|

                .. versionadded:: 21.7
            direct_messages_topic_id (:obj:`int`, optional): Identifier of the direct messages
                topic to which the messages will be sent; required if the messages are sent to a
                direct messages chat.

                .. versionadded:: 22.4


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
            caption (:obj:`str`, optional): Caption that will be added to the
                first element of :paramref:`media`, so that it will be used as caption for the
                whole media group.
                Defaults to :obj:`None`.

                .. versionadded:: 20.0
            parse_mode (:obj:`str` | :obj:`None`, optional):
                Parse mode for :paramref:`caption`.
                See the constants in :class:`telegram.constants.ParseMode` for the
                available modes.

                .. versionadded:: 20.0
            caption_entities (Sequence[:class:`telegram.MessageEntity`], optional):
                List of special entities for :paramref:`caption`,
                which can be specified instead of :paramref:`parse_mode`.
                Defaults to :obj:`None`.

                .. versionadded:: 20.0

        Returns:
            tuple[:class:`telegram.Message`]: An array of the sent Messages.
        """
        if caption and any(
            [
                any(item.caption for item in media),
                any(item.caption_entities for item in media),
                # if parse_mode was set explicitly, even to None, error must be raised
                any(item.parse_mode is not DEFAULT_NONE for item in media),
            ]
        ):
            raise ValueError("You can only supply either group caption or media with captions.")

        if caption:
            # Copy first item (to avoid mutation of original object), apply group caption to it.
            # This will lead to the group being shown with this caption.
            item_to_get_caption = copy.copy(media[0])
            with item_to_get_caption._unfrozen():
                item_to_get_caption.caption = caption
                if parse_mode is not DEFAULT_NONE:
                    item_to_get_caption.parse_mode = parse_mode
                item_to_get_caption.caption_entities = parse_sequence_arg(caption_entities)

            # copy the list (just the references) to avoid mutating the original list
            media = list(media)
            media[0] = item_to_get_caption

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
            "media": media,
            "disable_notification": disable_notification,
            "protect_content": protect_content,
            "message_thread_id": message_thread_id,
            "reply_parameters": reply_parameters,
            "business_connection_id": business_connection_id,
            "message_effect_id": message_effect_id,
            "allow_paid_broadcast": allow_paid_broadcast,
            "direct_messages_topic_id": direct_messages_topic_id,
        }

        result = await self._post(
            "sendMediaGroup",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        return Message.de_list(result, self)