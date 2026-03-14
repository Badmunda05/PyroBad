from __future__ import annotations

from typing import List, Optional

import pyrogram
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .rendering import export_entity_list
from .html import HTML
from .markdown import Markdown
from .types import ParseResult
from .utils import add_surrogates


class CombinedParser:
    def __init__(self, client: Optional["pyrogram.Client"]) -> None:
        self.client = client
        self.html = HTML(client)
        self.markdown = Markdown(client)

    async def parse(self, text: str) -> ParseResult:
        html_result = self.html._parse_entities(text)
        source = html_result["message"]
        html_entities = list(html_result["entities"] or [])

        message, markdown_entities = self.markdown._parse_entities(source)

        if html_entities:
            mapping = self._build_subsequence_map(add_surrogates(source), add_surrogates(message))
            html_entities = [self._remap_entity(entity, mapping) for entity in html_entities]

        entities = [*markdown_entities, *html_entities]
        entities.sort(key=lambda entity: (entity.offset, entity.length))

        return {
            "message": message,
            "entities": await export_entity_list(self.client, entities)
        }

    @staticmethod
    def _build_subsequence_map(source: str, plain: str) -> List[int]:
        mapping: List[int] = [0] * (len(source) + 1)
        plain_index = 0

        for source_index, char in enumerate(source):
            mapping[source_index] = plain_index

            if plain_index < len(plain) and char == plain[plain_index]:
                plain_index += 1

            mapping[source_index + 1] = plain_index

        return mapping

    @staticmethod
    def _remap_entity(entity: MessageEntity, mapping: List[int]) -> MessageEntity:
        start = mapping[entity.offset]
        end = mapping[entity.offset + entity.length]

        return MessageEntity(
            type=entity.type,
            offset=start,
            length=end - start,
            url=entity.url,
            user=entity.user,
            language=entity.language,
            custom_emoji_id=entity.custom_emoji_id,
            expandable=entity.expandable,
            unix_time=entity.unix_time,
            date_time_format=entity.date_time_format
        )
