def effective_message_type(entity: "Message | Update") -> str | None:
    """
    Extracts the type of message as a string identifier from a :class:`telegram.Message` or a
    :class:`telegram.Update`.

    Args:
        entity (:class:`telegram.Update` | :class:`telegram.Message`): The ``update`` or
            ``message`` to extract from.

    Returns:
        :obj:`str` | :obj:`None`: One of :class:`telegram.constants.MessageType` if the entity
        contains a message that matches one of those types. :obj:`None` otherwise.

    """
    # Importing on file-level yields cyclic Import Errors
    from telegram import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
        Message,
        Update,
    )

    if isinstance(entity, Message):
        message = entity
    elif isinstance(entity, Update):
        if not entity.effective_message:
            return None
        message = entity.effective_message
    else:
        raise TypeError(f"The entity is neither Message nor Update (got: {type(entity)})")

    for message_type in MessageType:
        if message[message_type]:
            return message_type

    return None