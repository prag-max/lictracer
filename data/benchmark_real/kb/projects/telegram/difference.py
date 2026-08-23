def difference(
        self,
    ) -> dict[
        str,
        tuple[str | bool | dtm.datetime | User, str | bool | dtm.datetime | User],
    ]:
        """Computes the difference between :attr:`old_chat_member` and :attr:`new_chat_member`.

        Example:
            .. code:: pycon

                >>> chat_member_updated.difference()
                {'custom_title': ('old title', 'new title')}

        Note:
            To determine, if the :attr:`telegram.ChatMember.user` attribute has changed, *every*
            attribute of the user will be checked.

        .. versionadded:: 13.5

        Returns:
            dict[:obj:`str`, tuple[:class:`object`, :class:`object`]]: A dictionary mapping
            attribute names to tuples of the form ``(old_value, new_value)``
        """
        # we first get the names of the attributes that have changed
        # user.to_dict() is unhashable, so that needs some special casing further down
        old_dict = self.old_chat_member.to_dict()
        old_user_dict = old_dict.pop("user")
        new_dict = self.new_chat_member.to_dict()
        new_user_dict = new_dict.pop("user")

        # Generator for speed: we only need to iterate over it once
        # we can't directly use the values from old_dict ^ new_dict b/c that set is unordered
        attributes = (entry[0] for entry in set(old_dict.items()) ^ set(new_dict.items()))

        result = {attribute: self._get_attribute_difference(attribute) for attribute in attributes}
        if old_user_dict != new_user_dict:
            result["user"] = (self.old_chat_member.user, self.new_chat_member.user)

        return result  # type: ignore[return-value]