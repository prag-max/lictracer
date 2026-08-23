@classmethod
    def de_json(cls, data: JSONDict, bot: "Bot | None" = None) -> "ChatFullInfo":
        """See :meth:`telegram.TelegramObject.de_json`."""
        data = cls._parse_data(data)

        # Get the local timezone from the bot if it has defaults
        loc_tzinfo = extract_tzinfo_from_defaults(bot)

        data["emoji_status_expiration_date"] = from_timestamp(
            data.get("emoji_status_expiration_date"), tzinfo=loc_tzinfo
        )

        data["photo"] = de_json_optional(data.get("photo"), ChatPhoto, bot)
        data["accepted_gift_types"] = de_json_optional(
            data.get("accepted_gift_types"), AcceptedGiftTypes, bot
        )

        from telegram import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            BusinessIntro,
            BusinessLocation,
            BusinessOpeningHours,
            Message,
        )

        data["pinned_message"] = de_json_optional(data.get("pinned_message"), Message, bot)
        data["permissions"] = de_json_optional(data.get("permissions"), ChatPermissions, bot)
        data["location"] = de_json_optional(data.get("location"), ChatLocation, bot)
        data["available_reactions"] = de_list_optional(
            data.get("available_reactions"), ReactionType, bot
        )
        data["birthdate"] = de_json_optional(data.get("birthdate"), Birthdate, bot)
        data["personal_chat"] = de_json_optional(data.get("personal_chat"), Chat, bot)
        data["business_intro"] = de_json_optional(data.get("business_intro"), BusinessIntro, bot)
        data["business_location"] = de_json_optional(
            data.get("business_location"), BusinessLocation, bot
        )
        data["business_opening_hours"] = de_json_optional(
            data.get("business_opening_hours"), BusinessOpeningHours, bot
        )
        data["parent_chat"] = de_json_optional(data.get("parent_chat"), Chat, bot)

        data["rating"] = de_json_optional(data.get("rating"), UserRating, bot)
        data["unique_gift_colors"] = de_json_optional(
            data.get("unique_gift_colors"), UniqueGiftColors, bot
        )
        data["first_profile_audio"] = de_json_optional(data.get("first_profile_audio"), Audio, bot)

        return super().de_json(data=data, bot=bot)