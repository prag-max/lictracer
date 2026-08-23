async def download_to_drive(
        self,
        custom_path: FilePathInput | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
    ) -> Path:
        """
        Download this file. By default, the file is saved in the current working directory with
        :attr:`file_path` as file name. If :paramref:`custom_path` is supplied as a :obj:`str` or
        :obj:`pathlib.Path`, it will be saved to that path.

        Note:
            If :paramref:`custom_path` isn't provided and :attr:`file_path` is the path of a
            local file (which is the case when a Bot API Server is running in local mode), this
            method will just return the path.

            The only exception to this are encrypted files (e.g. a passport file). For these, a
            file with the prefix `decrypted_` will be created in the same directory as the
            original file in order to decrypt the file without changing the existing one
            in-place.

        .. seealso:: :wiki:`Working with Files and Media <Working-with-Files-and-Media>`

        .. versionchanged:: 20.0

            * :paramref:`custom_path` parameter now also accepts :class:`pathlib.Path` as argument.
            * Returns :class:`pathlib.Path` object in cases where previously a :obj:`str` was
              returned.
            * This method was previously called ``download``. It was split into
              :meth:`download_to_drive` and :meth:`download_to_memory`.

        .. versionchanged:: 21.7
            Raises :exc:`RuntimeError` if :attr:`file_path` is not set. Note that files without
            a :attr:`file_path` could never be downloaded, as this attribute is mandatory for that
            operation.

        Args:
            custom_path (:class:`pathlib.Path` | :obj:`str` , optional): The path where the file
                will be saved to. If not specified, will be saved in the current working directory
                with :attr:`file_path` as file name or the :attr:`file_id` if :attr:`file_path`
                is not set.

        Keyword Args:
            read_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.read_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            write_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.write_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            connect_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.connect_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.
            pool_timeout (:obj:`float` | :obj:`None`, optional): Value to pass to
                :paramref:`telegram.request.BaseRequest.post.pool_timeout`. Defaults to
                :attr:`~telegram.request.BaseRequest.DEFAULT_NONE`.

        Returns:
            :class:`pathlib.Path`: Returns the Path object the file was downloaded to.

        Raises:
            RuntimeError: If :attr:`file_path` is not set.

        """

        local_file = is_local_file(self.file_path)
        url = None if local_file else self._get_encoded_url()

        # if _credentials exists we want to decrypt the file
        if local_file and self._credentials:
            file_to_decrypt = Path(self.file_path)
            buf = self._prepare_decrypt(file_to_decrypt.read_bytes())
            if custom_path is not None:
                path = Path(custom_path)
            else:
                path = Path(str(file_to_decrypt.parent) + "/decrypted_" + file_to_decrypt.name)
            path.write_bytes(buf)
            return path

        if custom_path is not None and local_file:
            shutil.copyfile(self.file_path, str(custom_path))
            return Path(custom_path)

        if custom_path:
            filename = Path(custom_path)
        elif local_file:
            return Path(self.file_path)
        else:
            filename = Path(Path(self.file_path).name)

        buf = await self.get_bot().request.retrieve(
            url,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
        )
        if self._credentials:
            buf = self._prepare_decrypt(buf)
        filename.write_bytes(buf)
        return filename