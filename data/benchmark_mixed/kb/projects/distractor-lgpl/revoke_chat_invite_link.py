async def revoke_chat_invite_link(
        self,
        chat_id: str | int,
        invite_link: "str | ChatInviteLink",
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot. If the primary link is
        revoked, a new link is automatically generated. The bot must be an administrator in the
        chat for this to work and must have the appropriate admin rights.

        .. versionadded:: 13.4

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            invite_link (:obj:`str` | :class:`telegram.ChatInviteLink`): The invite link to revoke.

                .. versionchanged:: 20.0
                    Now also accepts :class:`telegram.ChatInviteLink` instances.

        Returns:
            :class:`telegram.ChatInviteLink`
        """
        link = invite_link.invite_link if isinstance(invite_link, ChatInviteLink) else invite_link
        data: JSONDict = {"chat_id": chat_id, "invite_link": link}

        result = await self._post(
            "revokeChatInviteLink",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        return ChatInviteLink.de_json(result, self)