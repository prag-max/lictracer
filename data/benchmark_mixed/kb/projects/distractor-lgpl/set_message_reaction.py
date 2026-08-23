async def set_message_reaction(
        self,
        chat_id: str | int,
        message_id: int,
        reaction: Sequence[ReactionType | str] | ReactionType | str | None = None,
        is_big: bool | None = None,
        *,
        read_timeout: ODVInput[float] = DEFAULT_NONE,
        write_timeout: ODVInput[float] = DEFAULT_NONE,
        connect_timeout: ODVInput[float] = DEFAULT_NONE,
        pool_timeout: ODVInput[float] = DEFAULT_NONE,
        api_kwargs: JSONDict | None = None,
    ) -> bool:
        """
        Use this method to change the chosen reactions on a message. Service messages of some types
        can't be
        reacted to. Automatically forwarded messages from a channel to its discussion group have
        the same available reactions as messages in the channel. Bots can't use paid reactions.

        .. versionadded:: 20.8

        Args:
            chat_id (:obj:`int` | :obj:`str`): |chat_id_channel|
            message_id (:obj:`int`): Identifier of the target message. If the message belongs to a
                media group, the reaction is set to the first non-deleted message in the group
                instead.
            reaction (Sequence[:class:`telegram.ReactionType` | :obj:`str`] | \
                :class:`telegram.ReactionType` | :obj:`str`, optional): A list of reaction
                types to set on the message. Currently, as non-premium users, bots can set up to
                one reaction per message. A custom emoji reaction can be used if it is either
                already present on the message or explicitly allowed by chat administrators. Paid
                reactions can't be used by bots.

                Tip:
                    Passed :obj:`str` values will be converted to either
                    :class:`telegram.ReactionTypeEmoji` or
                    :class:`telegram.ReactionTypeCustomEmoji`
                    depending on whether they are listed in
                    :class:`~telegram.constants.ReactionEmoji`.

            is_big (:obj:`bool`, optional): Pass :obj:`True` to set the reaction with a big
                animation.

        Returns:
            :obj:`bool` On success, :obj:`True` is returned.
        """
        allowed_reactions: set[str] = set(ReactionEmoji)
        parsed_reaction = (
            [
                (
                    entry
                    if isinstance(entry, ReactionType)
                    else (
                        ReactionTypeEmoji(emoji=entry)
                        if entry in allowed_reactions
                        else ReactionTypeCustomEmoji(custom_emoji_id=entry)
                    )
                )
                for entry in ([reaction] if isinstance(reaction, ReactionType | str) else reaction)
            ]
            if reaction is not None
            else None
        )

        data: JSONDict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": parsed_reaction,
            "is_big": is_big,
        }

        return await self._post(
            "setMessageReaction",
            data,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            connect_timeout=connect_timeout,
            pool_timeout=pool_timeout,
            api_kwargs=api_kwargs,
        )