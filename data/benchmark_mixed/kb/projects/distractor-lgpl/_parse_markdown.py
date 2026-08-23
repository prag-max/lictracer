@classmethod
    def _parse_markdown(
        cls,
        message_text: str | None,
        entities: dict[MessageEntity, str],
        urled: bool = False,
        version: MarkdownVersion = 1,
        offset: int = 0,
    ) -> str | None:
        if version == 1:
            for entity_type in (
                MessageEntity.EXPANDABLE_BLOCKQUOTE,
                MessageEntity.BLOCKQUOTE,
                MessageEntity.CUSTOM_EMOJI,
                MessageEntity.SPOILER,
                MessageEntity.STRIKETHROUGH,
                MessageEntity.UNDERLINE,
                MessageEntity.DATE_TIME,
            ):
                if any(entity.type == entity_type for entity in entities):
                    name = entity_type.name.title().replace("_", " ")  # type:ignore[attr-defined]
                    raise ValueError(f"{name} entities are not supported for Markdown version 1")

        if message_text is None:
            return None

        utf_16_text = message_text.encode(TextEncoding.UTF_16_LE)
        markdown_text = ""
        last_offset = 0

        sorted_entities = sorted(entities.items(), key=lambda item: item[0].offset)
        parsed_entities = []

        for entity, text in sorted_entities:
            if entity in parsed_entities:
                continue

            nested_entities = {
                e: t
                for (e, t) in sorted_entities
                if e.offset >= entity.offset
                and e.offset + e.length <= entity.offset + entity.length
                and e != entity
            }
            parsed_entities.extend(list(nested_entities.keys()))

            if nested_entities:
                if version < 2:
                    raise ValueError("Nested entities are not supported for Markdown version 1")

                escaped_text = cls._parse_markdown(
                    text,
                    nested_entities,
                    urled=urled,
                    offset=entity.offset,
                    version=version,
                )
            else:
                escaped_text = escape_markdown(text, version=version)

            if entity.type == MessageEntity.TEXT_LINK:
                if version == 1:
                    url = entity.url
                else:
                    # Links need special escaping. Also can't have entities nested within
                    url = escape_markdown(
                        entity.url, version=version, entity_type=MessageEntity.TEXT_LINK
                    )
                insert = f"[{escaped_text}]({url})"
            elif entity.type == MessageEntity.TEXT_MENTION and entity.user:
                insert = f"[{escaped_text}](tg://user?id={entity.user.id})"
            elif entity.type == MessageEntity.URL and urled:
                link = text if version == 1 else escaped_text
                insert = f"[{link}]({text})"
            elif entity.type == MessageEntity.BOLD:
                insert = f"*{escaped_text}*"
            elif entity.type == MessageEntity.ITALIC:
                insert = f"_{escaped_text}_"
            elif entity.type == MessageEntity.CODE:
                # Monospace needs special escaping. Also can't have entities nested within
                insert = f"`{escape_markdown(text, version, MessageEntity.CODE)}`"
            elif entity.type == MessageEntity.PRE:
                # Monospace needs special escaping. Also can't have entities nested within
                code = escape_markdown(text, version=version, entity_type=MessageEntity.PRE)
                if entity.language:
                    prefix = f"```{entity.language}\n"
                elif code.startswith("\\"):
                    prefix = "```"
                else:
                    prefix = "```\n"
                insert = f"{prefix}{code}```"
            elif entity.type == MessageEntity.UNDERLINE:
                insert = f"__{escaped_text}__"
            elif entity.type == MessageEntity.STRIKETHROUGH:
                insert = f"~{escaped_text}~"
            elif entity.type == MessageEntity.SPOILER:
                insert = f"||{escaped_text}||"
            elif entity.type in (MessageEntity.BLOCKQUOTE, MessageEntity.EXPANDABLE_BLOCKQUOTE):
                insert = ">" + "\n>".join(escaped_text.splitlines())
                if entity.type == MessageEntity.EXPANDABLE_BLOCKQUOTE:
                    insert = f"{insert}||"
            elif entity.type == MessageEntity.CUSTOM_EMOJI:
                # This should never be needed because ids are numeric but the documentation
                # specifically mentions it so here we are
                custom_emoji_id = escape_markdown(
                    entity.custom_emoji_id,
                    version=version,
                    entity_type=MessageEntity.CUSTOM_EMOJI,
                )
                insert = f"![{escaped_text}](tg://emoji?id={custom_emoji_id})"
            elif entity.type == MessageEntity.DATE_TIME:
                if entity.date_time_format:
                    insert = (
                        f"![{escaped_text}](tg://time?unix={to_timestamp(entity.unix_time)}"
                        f"&format={entity.date_time_format})"
                    )
                else:
                    insert = f"![{escaped_text}](tg://time?unix={to_timestamp(entity.unix_time)})"
            else:
                insert = escaped_text

            # Make sure to escape the text that is not part of the entity
            # if we're in a nested entity, this is still required, since in that case this
            # text is part of the parent entity
            markdown_text += (
                escape_markdown(
                    utf_16_text[last_offset * 2 : (entity.offset - offset) * 2].decode(
                        TextEncoding.UTF_16_LE
                    ),
                    version=version,
                )
                + insert
            )

            last_offset = entity.offset - offset + entity.length

        # see comment above
        markdown_text += escape_markdown(
            utf_16_text[last_offset * 2 :].decode(TextEncoding.UTF_16_LE),
            version=version,
        )

        return markdown_text