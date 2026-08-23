async def send_location(
        self,
        chat_id: int | str,
        latitude: float | None = None,
        longitude: float | None = None,
        disable_notification: ODVInput[bool] = DEFAULT_NONE,
        reply_markup: "ReplyMarkup | None" = None,
        live_period: TimePeriod | None = None,
        horizontal_accuracy: float | None = None,
        heading: int | None = None,
        proximity_alert_radius: int | None = None,
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
        location: "Location | None" = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> Message:
        """Use this method to send point on the map.

        Note:
            You can either supply a :paramref:`latitude` and :paramref:`longitude` or a
            :paramref:`location`.

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            latitude (:obj:`float`, optional): Latitude of location.
            longitude (:obj:`float`, optional): Longitude of location.
            horizontal_accuracy (:obj:`int`, optional): The radius of uncertainty for the location,
                measured in meters;
                0-:tg-const:`telegram.constants.LocationLimit.HORIZONTAL_ACCURACY`.
            live_period (:obj:`int` | :class:`datetime.timedelta`, optional): Period in seconds for
                which the location will be
                updated, should be between
                :tg-const:`telegram.constants.LocationLimit.MIN_LIVE_PERIOD` and
                :tg-const:`telegram.constants.LocationLimit.MAX_LIVE_PERIOD`, or
                :tg-const:`telegram.constants.LocationLimit.LIVE_PERIOD_FOREVER` for live
                locations that can be edited indefinitely.

                .. versionchanged:: 21.11
                    |time-period-input|
            heading (:obj:`int`, optional): For live locations, a direction in which the user is
                moving, in degrees. Must be between
                :tg-const:`telegram.constants.LocationLimit.MIN_HEADING` and
                :tg-const:`telegram.constants.LocationLimit.MAX_HEADING` if specified.
            proximity_alert_radius (:obj:`int`, optional): For live locations, a maximum distance
                for proximity alerts about approaching another chat member, in meters. Must be
                between :tg-const:`telegram.constants.LocationLimit.MIN_PROXIMITY_ALERT_RADIUS`
                and :tg-const:`telegram.constants.LocationLimit.MAX_PROXIMITY_ALERT_RADIUS`
                if specified.
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
            location (:class:`telegram.Location`, optional): The location to send.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.
        """
        if not ((latitude is not None and longitude is not None) or location):
            raise ValueError(
                "Either location or latitude and longitude must be passed as argument."
            )

        if not (latitude is not None or longitude is not None) ^ bool(location):
            raise ValueError(
                "Either location or latitude and longitude must be passed as argument. Not both."
            )

        if isinstance(location, Location):
            latitude = location.latitude
            longitude = location.longitude

        data: JSONDict = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "horizontal_accuracy": horizontal_accuracy,
            "live_period": live_period,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
        }

        return await self._send_message(
            "sendLocation",
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