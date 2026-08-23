@staticmethod
    def _value_and_input_files_from_input(  # pylint: disable=too-many-return-statements
        value: object,
    ) -> tuple[object, list[InputFile]]:
        """Converts `value` into something that we can json-dump. Returns two values:
        1. the JSON-dumpable value. May be `None` in case the value is an InputFile which must
           not be uploaded via an attach:// URI
        2. A list of InputFiles that should be uploaded for this value

        Note that we handle files differently depending on whether attaching them via an URI of the
        form attach://<name> is documented to be allowed or not.
        There was some confusion whether this worked for all files, so that we stick to the
        documented ways for now.
        See https://github.com/tdlib/telegram-bot-api/issues/167 and
        https://github.com/tdlib/telegram-bot-api/issues/259

        This method only does some special casing for our own helper class StringEnum, but not
        for general enums. This is because:
        * tg.constants currently only uses IntEnum as second enum type and json dumping that
          is no problem
        * if a user passes a custom enum, it's unlikely that we can actually properly handle it
          even with some special casing.
        """
        if isinstance(value, dtm.datetime):
            return to_timestamp(value), []
        if isinstance(value, dtm.timedelta):
            seconds = value.total_seconds()
            # We convert to int for completeness for whole seconds
            if seconds.is_integer():
                return int(seconds), []
            # The Bot API doesn't document behavior for fractions of seconds so far, but we don't
            # want to silently drop them
            return seconds, []
        if isinstance(value, InputFile):
            if value.attach_uri:
                return value.attach_uri, [value]
            return None, [value]
        if isinstance(value, StringEnum):
            return value.value, []

        if isinstance(value, InputMedia | InputPaidMedia) and isinstance(value.media, InputFile):
            # We call to_dict and change the returned dict instead of overriding
            # value.media in case the same value is reused for another request
            data = value.to_dict()
            if value.media.attach_uri:
                data["media"] = value.media.attach_uri
            else:
                data.pop("media", None)

            thumbnail = data.get("thumbnail", None)
            if isinstance(thumbnail, InputFile):
                if thumbnail.attach_uri:
                    data["thumbnail"] = thumbnail.attach_uri
                else:
                    data.pop("thumbnail", None)
                return data, [value.media, thumbnail]

            return data, [value.media]

        if isinstance(value, InputProfilePhoto):
            attr = "photo" if isinstance(value, InputProfilePhotoStatic) else "animation"
            if not isinstance(media := getattr(value, attr), InputFile):
                # We don't have to upload anything
                return value.to_dict(), []

            # We call to_dict and change the returned dict instead of overriding
            # value.photo in case the same value is reused for another request
            data = value.to_dict()
            data[attr] = media.attach_uri
            return data, [media]

        if isinstance(value, InputStoryContent):
            attr = value.type
            if not isinstance(media := getattr(value, attr), InputFile):
                # We don't have to upload anything
                return value.to_dict(), []

            # We call to_dict and change the returned dict instead of overriding
            # value.photo in case the same value is reused for another request
            data = value.to_dict()
            data[attr] = media.attach_uri
            return data, [media]

        if isinstance(value, InputSticker) and isinstance(value.sticker, InputFile):
            # We call to_dict and change the returned dict instead of overriding
            # value.sticker in case the same value is reused for another request
            data = value.to_dict()
            data["sticker"] = value.sticker.attach_uri
            return data, [value.sticker]

        if isinstance(value, TelegramObject):
            # Needs to be last, because InputMedia is a subclass of TelegramObject
            return value.to_dict(), []
        return value, []