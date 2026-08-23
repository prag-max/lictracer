async def get_file(
        self,
        file_id: (
            str
            | Animation
            | Audio
            | ChatPhoto
            | Document
            | PhotoSize
            | Sticker
            | Video
            | VideoNote
            | Voice
        ),
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> File:
        """
        Use this method to get basic info about a file and prepare it for downloading. For the
        moment, bots can download files of up to
        :tg-const:`telegram.constants.FileSizeLimit.FILESIZE_DOWNLOAD` in size. The file can then
        be e.g. downloaded with :meth:`telegram.File.download_to_drive`. It is guaranteed that
        the link will be valid for at least 1 hour. When the link expires, a new one can be
        requested by calling get_file again.

        Note:
            This function may not preserve the original file name and MIME type.
            You should save the file's MIME type and name (if available) when the File object
            is received.

        .. seealso:: :wiki:`Working with Files and Media <Working-with-Files-and-Media>`

        Args:
            file_id (:obj:`str` | :class:`telegram.Animation` | :class:`telegram.Audio` |         \
                     :class:`telegram.ChatPhoto` | :class:`telegram.Document` |                   \
                     :class:`telegram.PhotoSize` | :class:`telegram.Sticker` |                    \
                     :class:`telegram.Video` | :class:`telegram.VideoNote` |                      \
                     :class:`telegram.Voice`):
                Either the file identifier or an object that has a file_id attribute
                to get file information about.

        Returns:
            :class:`telegram.File`
        """
        # Try to get the file_id from the object, if it fails, assume it's a string
        with contextlib.suppress(AttributeError):
            file_id = file_id.file_id  # type: ignore[union-attr]

        data: JSONDict = {"file_id": file_id}

        result = await self._post(
            "getFile",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        file_path = cast("dict", result).get("file_path")
        if file_path and not is_local_file(file_path):
            result["file_path"] = f"{self._base_file_url}/{file_path}"

        return File.de_json(result, self)