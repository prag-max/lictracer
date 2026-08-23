async def edit_chat_invite_link(
        self,
        chat_id: str | int,
        invite_link: "str | ChatInviteLink",
        expire_date: int | dtm.datetime | None = None,
        member_limit: int | None = None,
        name: str | None = None,
        creates_join_request: bool | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot. The bot must be an
        administrator in the chat for this to work and must have the appropriate admin rights.

        Note:
            Though not stated explicitly in the official docs, Telegram changes not only the
            optional parameters that are explicitly passed, but also replaces all other optional
            parameters to the default values. However, since not documented, this behaviour may
            change unbeknown to PTB.

        .. versionadded:: 13.4

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            invite_link (:obj:`str` | :class:`telegram.ChatInviteLink`): The invite link to edit.

                .. versionchanged:: 20.0
                    Now also accepts :class:`telegram.ChatInviteLink` instances.
            expire_date (:obj:`int` | :obj:`datetime.datetime`, optional): Date when the link will
                expire.
                |tz-naive-dtms|
            member_limit (:obj:`int`, optional): Maximum number of users that can be members of
                the chat simultaneously after joining the chat via this invite link;
                :tg-const:`telegram.constants.ChatInviteLinkLimit.MIN_MEMBER_LIMIT`-
                :tg-const:`telegram.constants.ChatInviteLinkLimit.MAX_MEMBER_LIMIT`.
            name (:obj:`str`, optional): Invite link name;
                0-:tg-const:`telegram.constants.ChatInviteLinkLimit.NAME_LENGTH` characters.

                .. versionadded:: 13.8
            creates_join_request (:obj:`bool`, optional): :obj:`True`, if users joining the chat
                via the link need to be approved by chat administrators.
                If :obj:`True`, :paramref:`member_limit` can't be specified.

                .. versionadded:: 13.8

        Returns:
            :class:`telegram.ChatInviteLink`
        """
        link = invite_link.invite_link if isinstance(invite_link, ChatInviteLink) else invite_link
        data: JSONDict = {
            "chat_id": chat_id,
            "invite_link": link,
            "expire_date": expire_date,
            "member_limit": member_limit,
            "name": name,
            "creates_join_request": creates_join_request,
        }

        result = await self._post(
            "editChatInviteLink",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        return ChatInviteLink.de_json(result, self)