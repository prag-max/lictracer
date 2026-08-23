@property
    def effective_sender(self) -> "User | Chat | None":
        """
        :class:`telegram.User` or :class:`telegram.Chat`: The user or chat that sent this update,
        no matter what kind of update this is.

        Note:
            * Depending on the type of update and the user's 'Remain anonymous' setting, this
              could either be :class:`telegram.User`, :class:`telegram.Chat` or :obj:`None`.

        If no user whatsoever is associated with this update, this gives :obj:`None`. This
        is the case if any of

        * :attr:`poll`
        * :attr:`chat_boost`
        * :attr:`removed_chat_boost`
        * :attr:`message_reaction_count`
        * :attr:`deleted_business_messages`

        is present.

        .. versionchanged:: 22.8
            This property now also considers :attr:`guest_message`.

        Example:
            * If :attr:`message` is present, this will give either
              :attr:`telegram.Message.from_user` or :attr:`telegram.Message.sender_chat`.
            * If :attr:`poll_answer` is present, this will give either
              :attr:`telegram.PollAnswer.user` or :attr:`telegram.PollAnswer.voter_chat`.
            * If :attr:`channel_post` is present, this will give
              :attr:`telegram.Message.sender_chat`.

        .. versionadded:: 21.1
        """
        if self._effective_sender:
            return self._effective_sender

        sender: User | Chat | None = None

        if message := (
            self.message
            or self.edited_message
            or self.channel_post
            or self.edited_channel_post
            or self.business_message
            or self.edited_business_message
            or self.guest_message
        ):
            sender = message.sender_chat

        elif self.poll_answer:
            sender = self.poll_answer.voter_chat

        elif self.message_reaction:
            sender = self.message_reaction.actor_chat

        if sender is None:
            sender = self.effective_user

        self._effective_sender = sender
        return sender