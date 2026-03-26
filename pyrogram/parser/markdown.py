from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pyrogram
from pyrogram import enums
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .rendering import export_entity_list, markdown_entity_rank, shift_entities
from .types import EntityMeta, MentionUserRef, ParseResult
from .utils import add_surrogates, remove_surrogates


CUSTOM_EMOJI_RE = re.compile(r"^tg://emoji\?id=(\d+)$")
DATE_TIME_RE = re.compile(r"^tg://time\?unix=(\d+)(?:&format=(r|w?[dD]?[tT]?))?$")
USER_LINK_RE = re.compile(r"^tg://user\?id=(\d+)$")


@dataclass
class _InlineDelimiter:
    token: str
    entity_type: enums.MessageEntityType
    meta: Optional[EntityMeta] = None


class Markdown:
    INLINE_TOKENS = {
        "**": enums.MessageEntityType.BOLD,
        "__": enums.MessageEntityType.ITALIC,
        "--": enums.MessageEntityType.UNDERLINE,
        "~~": enums.MessageEntityType.STRIKETHROUGH,
        "||": enums.MessageEntityType.SPOILER,
    }

    def __init__(self, client: Optional["pyrogram.Client"]) -> None:
        self.client = client

    async def parse(self, text: str) -> ParseResult:
        message, entities = self._parse_entities(text)

        return {
            "message": message,
            "entities": await export_entity_list(self.client, entities or [])
        }

    def _parse_entities(self, text: str) -> Tuple[str, List[MessageEntity]]:
        message, entities = self._parse_blocks(add_surrogates(text))
        entities.sort(key=lambda entity: (entity.offset, entity.length))
        return remove_surrogates(message), entities

    @staticmethod
    def unparse(text: str, entities: List[MessageEntity]) -> str:
        if not entities:
            return text

        source = add_surrogates(text)
        starts: Dict[int, List[MessageEntity]] = {}
        ends: Dict[int, List[MessageEntity]] = {}

        for entity in entities:
            starts.setdefault(entity.offset, []).append(entity)
            ends.setdefault(entity.offset + entity.length, []).append(entity)

        def entity_priority(entity: MessageEntity) -> int:
            return markdown_entity_rank(entity)

        def open_token(entity: MessageEntity) -> str:
            if entity.type == enums.MessageEntityType.BOLD:
                return "**"
            if entity.type == enums.MessageEntityType.ITALIC:
                return "__"
            if entity.type == enums.MessageEntityType.UNDERLINE:
                return "--"
            if entity.type == enums.MessageEntityType.STRIKETHROUGH:
                return "~~"
            if entity.type == enums.MessageEntityType.SPOILER:
                return "||"
            if entity.type in (
                enums.MessageEntityType.TEXT_LINK,
                enums.MessageEntityType.TEXT_MENTION,
                enums.MessageEntityType.EMAIL,
            ):
                return "["
            if entity.type in (
                enums.MessageEntityType.CUSTOM_EMOJI,
                enums.MessageEntityType.DATE_TIME
            ):
                return "!["
            if entity.type == enums.MessageEntityType.CODE:
                return "`"
            if entity.type == enums.MessageEntityType.PRE:
                return f"```{entity.language or ''}\n"
            return ""

        def close_token(entity: MessageEntity) -> str:
            if entity.type == enums.MessageEntityType.BOLD:
                return "**"
            if entity.type == enums.MessageEntityType.ITALIC:
                return "__"
            if entity.type == enums.MessageEntityType.UNDERLINE:
                return "--"
            if entity.type == enums.MessageEntityType.STRIKETHROUGH:
                return "~~"
            if entity.type == enums.MessageEntityType.SPOILER:
                return "||"
            if entity.type == enums.MessageEntityType.EMAIL:
                return f"](mailto:{remove_surrogates(source[entity.offset:entity.offset + entity.length])})"
            if entity.type == enums.MessageEntityType.TEXT_LINK:
                return f"]({entity.url or ''})"
            if entity.type == enums.MessageEntityType.TEXT_MENTION:
                if entity.user is None:
                    return "]()"
                return f"](tg://user?id={entity.user.id})"
            if entity.type == enums.MessageEntityType.CUSTOM_EMOJI:
                return f"](tg://emoji?id={entity.custom_emoji_id})"
            if entity.type == enums.MessageEntityType.DATE_TIME:
                target = f"tg://time?unix={entity.unix_time}"
                if entity.date_time_format:
                    target += f"&format={entity.date_time_format}"
                return f"]({target})"
            if entity.type == enums.MessageEntityType.CODE:
                return "`"
            if entity.type == enums.MessageEntityType.PRE:
                return "\n```"
            return ""

        parts: List[str] = []
        active_blockquotes: List[MessageEntity] = []

        for index in range(len(source) + 1):
            for entity in sorted(
                ends.get(index, []),
                key=lambda item: (-item.length, entity_priority(item))
            ):
                if entity.type == enums.MessageEntityType.BLOCKQUOTE:
                    if entity.expandable:
                        parts.append("||")
                    active_blockquotes = [item for item in active_blockquotes if item is not entity]
                else:
                    parts.append(close_token(entity))

            for entity in sorted(
                starts.get(index, []),
                key=lambda item: (-item.length, entity_priority(item))
            ):
                if entity.type == enums.MessageEntityType.BLOCKQUOTE:
                    active_blockquotes.append(entity)

            if index == len(source):
                break

            if index == 0 or source[index - 1] == "\n":
                for entity in active_blockquotes:
                    if entity.expandable and entity.offset == index:
                        parts.append("**> ")
                    else:
                        parts.append("> ")

            for entity in sorted(
                starts.get(index, []),
                key=lambda item: (-item.length, entity_priority(item))
            ):
                if entity.type != enums.MessageEntityType.BLOCKQUOTE:
                    parts.append(open_token(entity))

            parts.append(source[index])

        return remove_surrogates("".join(parts))

    def _parse_blocks(self, text: str) -> Tuple[str, List[MessageEntity]]:
        output: List[str] = []
        entities: List[MessageEntity] = []
        index = 0

        while index < len(text):
            if self._is_line_start(text, index) and text.startswith("```", index):
                plain, block_entities, index = self._consume_pre(text, index)
                base = len("".join(output))
                output.append(plain)
                entities.extend(shift_entities(block_entities, base))
                continue

            if self._is_line_start(text, index) and self._starts_blockquote(text, index):
                plain, block_entities, index = self._consume_blockquote(text, index)
                base = len("".join(output))
                output.append(plain)
                entities.extend(shift_entities(block_entities, base))
                continue

            boundary = self._find_next_block_boundary(text, index)
            plain, inline_entities = self._parse_inline(text[index:boundary])
            base = len("".join(output))
            output.append(plain)
            entities.extend(shift_entities(inline_entities, base))
            index = boundary

        return "".join(output), entities

    def _parse_inline(self, text: str) -> Tuple[str, List[MessageEntity]]:
        output: List[str] = []
        entities: List[MessageEntity] = []
        stack: List[_InlineDelimiter] = []
        positions: List[int] = []
        index = 0

        while index < len(text):
            if text[index] == "\\" and index + 1 < len(text):
                output.append(text[index + 1])
                index += 2
                continue

            if text.startswith("![", index):
                match = self._consume_link(text, index, emoji=True)
                if match:
                    plain, entity, index = match
                    start = len("".join(output))
                    output.append(plain)
                    if entity is not None:
                        entity.offset = start
                        entities.append(entity)
                    continue
                output.append(text[index])
                index += 1
                continue

            if text[index] == "[" and (index == 0 or text[index - 1] != "!"):
                match = self._consume_link(text, index, emoji=False)
                if match:
                    plain, entity, index = match
                    start = len("".join(output))
                    output.append(plain)
                    if entity is not None:
                        entity.offset = start
                        entities.append(entity)
                    continue

            if text[index] == "`":
                code = self._consume_inline_code(text, index)
                if code:
                    plain, entity, index = code
                    start = len("".join(output))
                    output.append(plain)
                    entity.offset = start
                    entities.append(entity)
                    continue

            token = self._match_inline_token(text, index)
            if token:
                if stack and stack[-1].token == token:
                    opened = stack.pop()
                    start = positions.pop()
                    entity = MessageEntity(
                        type=opened.entity_type,
                        offset=start,
                        length=len("".join(output)) - start,
                        **(opened.meta or {})
                    )
                    if entity.length > 0:
                        entities.append(entity)
                else:
                    stack.append(_InlineDelimiter(token=token, entity_type=self.INLINE_TOKENS[token]))
                    positions.append(len("".join(output)))

                index += len(token)
                continue

            output.append(text[index])
            index += 1

        while stack:
            token = stack.pop().token
            position = positions.pop()
            output.insert(position, token)

        entities.sort(key=lambda entity: (entity.offset, entity.length))
        return "".join(output), entities

    def _consume_pre(self, text: str, index: int) -> Tuple[str, List[MessageEntity], int]:
        start = index + 3
        newline = text.find("\n", start)

        if newline == -1:
            return self._parse_inline(text[index:])

        language = text[start:newline]
        end = text.find("```", newline + 1)

        if end == -1:
            return self._parse_inline(text[index:])

        content = text[newline + 1:end]
        entity = MessageEntity(
            type=enums.MessageEntityType.PRE,
            offset=0,
            length=len(content),
            language=remove_surrogates(language) or ""
        )
        return content, [entity], end + 3

    def _consume_blockquote(self, text: str, index: int) -> Tuple[str, List[MessageEntity], int]:
        lines: List[str] = []
        cursor = index
        expandable = text.startswith("**>", index)

        while cursor < len(text):
            line_end = text.find("\n", cursor)
            if line_end == -1:
                line_end = len(text)

            line = text[cursor:line_end]
            prefix = "**>" if expandable and cursor == index else ">"
            if not line.startswith(prefix):
                break

            content = line[len(prefix):]
            if content.startswith(" "):
                content = content[1:]
            closing = False
            if expandable and content.endswith("||"):
                content = content[:-2]
                closing = True
            lines.append(content)

            if line_end == len(text):
                cursor = len(text)
                break

            if closing:
                cursor = line_end + 1
                break

            next_cursor = line_end + 1
            if next_cursor < len(text) and text[next_cursor] != ">":
                cursor = next_cursor
                break

            cursor = next_cursor

        plain, inline_entities = self._parse_inline("\n".join(lines))
        blockquote = MessageEntity(
            type=enums.MessageEntityType.BLOCKQUOTE,
            offset=0,
            length=len(plain),
            expandable=expandable or None
        )
        return plain, [blockquote, *inline_entities], cursor

    def _consume_link(
        self,
        text: str,
        index: int,
        emoji: bool
    ) -> Optional[Tuple[str, MessageEntity, int]]:
        prefix = "![" if emoji else "["
        start = index + len(prefix)
        middle = text.find("](", start)

        if middle == -1:
            return None

        end = text.find(")", middle + 2)
        if end == -1:
            return None

        label = text[start:middle]
        target = remove_surrogates(text[middle + 2:end])

        if emoji:
            match = CUSTOM_EMOJI_RE.match(target)
            if match:
                entity = MessageEntity(
                    type=enums.MessageEntityType.CUSTOM_EMOJI,
                    offset=0,
                    length=len(label),
                    custom_emoji_id=int(match.group(1))
                )
            else:
                match = DATE_TIME_RE.match(target)
                if not match:
                    return None

                entity = MessageEntity(
                    type=enums.MessageEntityType.DATE_TIME,
                    offset=0,
                    length=len(label),
                    unix_time=int(match.group(1)),
                    date_time_format=match.group(2) or None
                )
        else:
            mention_match = USER_LINK_RE.match(target)
            if mention_match:
                entity = MessageEntity(
                    type=enums.MessageEntityType.TEXT_MENTION,
                    offset=0,
                    length=len(label),
                    user=MentionUserRef(id=int(mention_match.group(1)))
                )
            else:
                entity = MessageEntity(
                    type=enums.MessageEntityType.TEXT_LINK,
                    offset=0,
                    length=len(label),
                    url=target
                )

        return label, entity, end + 1

    def _consume_inline_code(self, text: str, index: int) -> Optional[Tuple[str, MessageEntity, int]]:
        end = text.find("`", index + 1)
        if end == -1:
            return None

        content = text[index + 1:end]
        entity = MessageEntity(
            type=enums.MessageEntityType.CODE,
            offset=0,
            length=len(content)
        )
        return content, entity, end + 1

    def _match_inline_token(self, text: str, index: int) -> Optional[str]:
        for token in ("**", "__", "--", "~~", "||"):
            if text.startswith(token, index):
                return token
        return None


    @staticmethod
    def _is_line_start(text: str, index: int) -> bool:
        return index == 0 or text[index - 1] == "\n"

    @staticmethod
    def _find_next_block_boundary(text: str, index: int) -> int:
        cursor = index + 1

        while cursor < len(text):
            if text[cursor - 1] == "\n" and (
                text.startswith("```", cursor)
                or text[cursor] == ">"
                or text.startswith("**>", cursor)
            ):
                return cursor
            cursor += 1

        return len(text)

    def _starts_blockquote(self, text: str, index: int) -> bool:
        if text[index] == ">":
            return True

        if not text.startswith("**>", index):
            return False

        cursor = index

        while cursor < len(text):
            line_end = text.find("\n", cursor)
            if line_end == -1:
                line_end = len(text)

            line = text[cursor:line_end]
            prefix = "**>" if cursor == index else ">"
            if not line.startswith(prefix):
                return False

            content = line[len(prefix):]
            if content.startswith(" "):
                content = content[1:]

            if content.endswith("||"):
                return True

            if line_end == len(text):
                return False

            cursor = line_end + 1

        return False
