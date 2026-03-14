from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from pyrogram import enums
from pyrogram.types.list import List as TypesList
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .specs import ENTITY_SPECS, HTML_ENTITY_ORDER, MARKDOWN_ENTITY_ORDER, EntitySpec
from .types import EntityNode
from .utils import add_surrogates, remove_surrogates


def make_entity_list(entities: Iterable[MessageEntity]) -> Optional[TypesList]:
    items = [entity for entity in entities if entity is not None and entity.length > 0]
    if not items:
        return None

    return TypesList(items)


async def export_entity_list(client, entities: Iterable[MessageEntity]) -> Optional[TypesList]:
    items = [entity for entity in entities if entity is not None and entity.length > 0]
    if not items:
        return None

    if client is None:
        return TypesList(items)

    for entity in items:
        entity._client = client

    return TypesList([await entity.write() for entity in items])


def shift_entities(entities: Iterable[MessageEntity], offset: int) -> List[MessageEntity]:
    shifted: List[MessageEntity] = []

    for entity in entities:
        shifted.append(MessageEntity(
            type=entity.type,
            offset=entity.offset + offset,
            length=entity.length,
            url=entity.url,
            user=entity.user,
            language=entity.language,
            custom_emoji_id=entity.custom_emoji_id,
            expandable=entity.expandable,
            unix_time=entity.unix_time,
            date_time_format=entity.date_time_format
        ))

    return shifted


def build_entity_tree(
    entities: Iterable[MessageEntity],
    rank_getter: Callable[[MessageEntity], int]
) -> List[EntityNode]:
    items = []

    for entity in entities:
        if entity.length <= 0:
            continue

        if ENTITY_SPECS.get(entity.type) is None:
            continue

        items.append((entity.offset, entity.offset + entity.length, rank_getter(entity), entity))

    items.sort(key=lambda item: (item[0], -item[1], item[2]))
    root = EntityNode(entity=None, start=0, end=10 ** 9)
    stack = [root]

    for start, end, _, entity in items:
        while len(stack) > 1 and start >= stack[-1].end:
            stack.pop()

        node = EntityNode(entity=entity, start=start, end=end)
        stack[-1].children.append(node)
        stack.append(node)

    return root.children


def render_entities(
    text: str,
    entities: Iterable[MessageEntity],
    formatter: Callable[[EntitySpec, str, MessageEntity], str],
    rank_getter: Callable[[MessageEntity], int],
    escape_text: Callable[[str], str]
) -> str:
    source = add_surrogates(text)
    tree = build_entity_tree(entities, rank_getter)

    def render_segment(start: int, end: int, children: List[EntityNode]) -> str:
        chunks: List[str] = []
        cursor = start

        for child in children:
            if cursor < child.start:
                chunks.append(escape_text(source[cursor:child.start]))

            spec = ENTITY_SPECS[child.entity.type]
            inner = render_segment(child.start, child.end, child.children)
            chunks.append(formatter(spec, inner, child.entity))
            cursor = child.end

        if cursor < end:
            chunks.append(escape_text(source[cursor:end]))

        return "".join(chunks)

    return remove_surrogates(render_segment(0, len(source), tree))


def html_entity_rank(entity: MessageEntity) -> int:
    return _entity_rank(entity, HTML_ENTITY_ORDER)


def markdown_entity_rank(entity: MessageEntity) -> int:
    return _entity_rank(entity, MARKDOWN_ENTITY_ORDER)


def _entity_rank(entity: MessageEntity, ordered_types: tuple[enums.MessageEntityType, ...]) -> int:
    try:
        return ordered_types.index(entity.type)
    except ValueError:
        return len(ordered_types)
