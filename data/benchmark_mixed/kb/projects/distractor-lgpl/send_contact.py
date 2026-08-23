async def send_contact(
        self,
        chat_id: int | str,
        phone_number: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        reply_markup: "ReplyMarkup | None" = None,
        vcard: str | None = None,
        protect_content: ODVInput[bool] = DEFAULT_NONE,
        message_thread_id: int | None = None,
        reply_parameters: "ReplyParameters | None" = None,
        business_connection_id: str | None = None,
        message_effect_id: str | None = None,
        allow_paid_broadcast: bool | None = None,
        direct_messages_topic_id: int | None = None,
        suggested_post_parameters: "SuggestedPostParameters | None" = None,
        *,
        allow_sending_without_reply: ODVInput[bool] = DEFAULT_NONE,
        reply_to_message_id: int | None = None,
        contact: "Contact | None" = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> Message:
        """Use this method to send phone contacts.

        Note:
            You can either supply :paramref:`contact` or :paramref:`phone_number` and
            :paramref:`first_name` with optionally :paramref:`last_name` and optionally
            :paramref:`vcard`.

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            phone_number (:obj:`str`, optional): Contact's phone number.
            first_name (:obj:`str`, optional): Contact's first name.
            last_name (:obj:`str`, optional): Contact's last name.
            vcard (:obj:`str`, optional): Additional data about the contact in the form of a vCard,
                0-:tg-const:`telegram.constants.ContactLimit.VCARD` bytes.
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
            business_connection_id (:obj:`str`, optional): |business_id_str|

                .. versionadded:: 21.1
            message_effect_id (:obj:`str`, optional): |message_effect_id|

                .. versionadded:: 21.3
            allow_paid_broadcast (:obj:`bool`, optional): |allow_paid_broadcast|

                .. versionadded:: 21.7
            suggested_post_parameters (:class:`telegram.SuggestedPostParameters`, optional):
                |suggested_post_parameters|

                .. versionadded:: 22.4
            direct_messages_topic_id (:obj:`int`, optional): |direct_messages_topic_id|

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
            contact (:class:`telegram.Contact`, optional): The contact to send.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.
        """
        # The contact parameter is a convenience functionality added by us, so enforcing the
        # mutual exclusivity here is nothing that Telegram would handle anyway
        if (not contact) and (not all([phone_number, first_name])):
            raise ValueError(
                "Either contact or phone_number and first_name must be passed as arguments."
            )
        if not bool(contact) ^ any([phone_number, first_name]):
            raise ValueError(
                "Either contact or phone_number and first_name must be passed as arguments. "
                "Not both."
            )

        if isinstance(contact, Contact):
            phone_number = contact.phone_number
            first_name = contact.first_name
            last_name = contact.last_name
            vcard = contact.vcard

        data: JSONDict = {
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "vcard": vcard,
        }

        return await self._send_message(
            "sendContact",
            data,
            reply_to_message_id=reply_to_message_id,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            protect_content=protect_content,
            message_thread_id=message_thread_id,
            reply_parameters=reply_parameters,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
            business_connection_id=business_connection_id,
            message_effect_id=message_effect_id,
            allow_paid_broadcast=allow_paid_broadcast,
            direct_messages_topic_id=direct_messages_topic_id,
            suggested_post_parameters=suggested_post_parameters,
        )