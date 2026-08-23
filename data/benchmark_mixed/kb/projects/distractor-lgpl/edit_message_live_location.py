async def edit_message_live_location(
        self,
        chat_id: str | int | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        reply_markup: "InlineKeyboardMarkup | None" = None,
        horizontal_accuracy: float | None = None,
        heading: int | None = None,
        proximity_alert_radius: int | None = None,
        live_period: TimePeriod | None = None,
        business_connection_id: str | None = None,
        *,
        location: "Location | None" = None,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> "Message | bool":
        """Use this method to edit live location messages sent by the bot or via the bot
        (for inline bots). A location can be edited until its :attr:`telegram.Location.live_period`
        expires or editing is explicitly disabled by a call to :meth:`stop_message_live_location`.

        Note:
            You can either supply a :paramref:`latitude` and :paramref:`longitude` or a
            :paramref:`location`.

        Args:
            chat_id (:obj:`int` | :obj:`str`, optional): Required if :paramref:`inline_message_id`
                is not specified. |chat_id_channel|
            message_id (:obj:`int`, optional): Required if :paramref:`inline_message_id` is not
                specified. Identifier of the message to edit.
            inline_message_id (:obj:`str`, optional): Required if :paramref:`chat_id` and
                :paramref:`message_id` are not specified. Identifier of the inline message.
            latitude (:obj:`float`, optional): Latitude of location.
            longitude (:obj:`float`, optional): Longitude of location.
            horizontal_accuracy (:obj:`float`, optional): The radius of uncertainty for the
                location, measured in meters;
                0-:tg-const:`telegram.constants.LocationLimit.HORIZONTAL_ACCURACY`.
            heading (:obj:`int`, optional): Direction in which the user is moving, in degrees. Must
                be between :tg-const:`telegram.constants.LocationLimit.MIN_HEADING`
                and :tg-const:`telegram.constants.LocationLimit.MAX_HEADING` if specified.
            proximity_alert_radius (:obj:`int`, optional): Maximum distance for proximity alerts
                about approaching another chat member, in meters. Must be between
                :tg-const:`telegram.constants.LocationLimit.MIN_PROXIMITY_ALERT_RADIUS`
                and :tg-const:`telegram.constants.LocationLimit.MAX_PROXIMITY_ALERT_RADIUS`
                if specified.
            reply_markup (:class:`telegram.InlineKeyboardMarkup`, optional): An object for a new
                inline keyboard.
            live_period (:obj:`int` | :class:`datetime.timedelta`, optional): New period in seconds
                during which the location
                can be updated, starting from the message send date. If
                :tg-const:`telegram.constants.LocationLimit.LIVE_PERIOD_FOREVER` is specified,
                then the location can be updated forever. Otherwise, the new value must not exceed
                the current ``live_period`` by more than a day, and the live location expiration
                date must remain within the next 90 days. If not specified, then ``live_period``
                remains unchanged

                .. versionadded:: 21.2.

                .. versionchanged:: 21.11
                    |time-period-input|
            business_connection_id (:obj:`str`, optional): |business_id_str_edit|

                .. versionadded:: 21.4

        Keyword Args:
            location (:class:`telegram.Location`, optional): The location to send.

        Returns:
            :class:`telegram.Message`: On success, if edited message is not an inline message, the
            edited message is returned, otherwise :obj:`True` is returned.
        """
        # The location parameter is a convenience functionality added by us, so enforcing the
        # mutual exclusivity here is nothing that Telegram would handle anyway
        if not (all([latitude, longitude]) or location):
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
            "latitude": latitude,
            "longitude": longitude,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "horizontal_accuracy": horizontal_accuracy,
            "heading": heading,
            "proximity_alert_radius": proximity_alert_radius,
            "live_period": live_period,
        }

        return await self._send_message(
            "editMessageLiveLocation",
            data,
            reply_markup=reply_markup,
            business_connection_id=business_connection_id,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )