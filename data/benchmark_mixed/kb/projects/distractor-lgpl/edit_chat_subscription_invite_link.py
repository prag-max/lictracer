async def edit_chat_subscription_invite_link(
        self,
        chat_id: str | int,
        invite_link: "str | ChatInviteLink",
        name: str | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a subscription invite link created by the bot. The bot must have
        :attr:`telegram.ChatPermissions.can_invite_users` administrator right.

        .. versionadded:: 21.5

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            invite_link (:obj:`str` | :obj:`telegram.ChatInviteLink`): The invite link to edit.
            name (:obj:`str`, optional): Invite link name;
                0-:tg-const:`telegram.constants.ChatInviteLinkLimit.NAME_LENGTH` characters.

                Tip:
                    Omitting this argument removes the name of the invite link.

        Returns:
            :class:`telegram.ChatInviteLink`
        """
        link = invite_link.invite_link if isinstance(invite_link, ChatInviteLink) else invite_link
        data: JSONDict = {
            "chat_id": chat_id,
            "invite_link": link,
            "name": name,
        }

        result = await self._post(
            "editChatSubscriptionInviteLink",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )

        return ChatInviteLink.de_json(result, self)