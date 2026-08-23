async def download_to_memory(
        self,
        out: BinaryIO,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
    ) -> None:
        """
        Download this file into memory. :paramref:`out` needs to be supplied with a
        :obj:`io.BufferedIOBase`, the file contents will be saved to that object using the
        :obj:`out.write<io.BufferedIOBase.write>` method.

        .. seealso:: :wiki:`Working with Files and Media <Working-with-Files-and-Media>`

        Hint:
            If you want to immediately read the data from ``out`` after calling this method, you
            should call ``out.seek(0)`` first. See also :meth:`io.IOBase.seek`.

        .. versionadded:: 20.0

        .. versionchanged:: 21.7
            Raises :exc:`RuntimeError` if :attr:`file_path` is not set. Note that files without
            a :attr:`file_path` could never be downloaded, as this attribute is mandatory for that
            operation.

        Args:
            out (:obj:`io.BufferedIOBase`): A file-like object. Must be opened for writing in
                binary mode.

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

        Raises:
            RuntimeError: If :attr:`file_path` is not set.
        """
        if not self.file_path:
            raise RuntimeError("No `file_path` available for this file. Can not download.")

        local_file = is_local_file(self.file_path)
        url = None if local_file else self._get_encoded_url()
        path = Path(self.file_path) if local_file else None
        if local_file:
            buf = path.read_bytes()
        else:
            buf = await self.get_bot().request.retrieve(
                url,
                read_timeout=read_timeout,
                write_timeout=write_timeout,
                connect_timeout=connect_timeout,
                pool_timeout=pool_timeout,
            )
        if self._credentials:
            buf = self._prepare_decrypt(buf)
        out.write(buf)