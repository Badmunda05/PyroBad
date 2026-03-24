from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import html
import re
from typing import Dict, Optional

from pyrogram import enums
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .types import EntityMeta, MentionUserRef


class EntitySpec(ABC):
    entity_type: Optional[enums.MessageEntityType] = None
    html_tags: tuple[str, ...] = ()

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        return {}

    def from_markdown_meta(self, meta: Optional[EntityMeta] = None) -> Optional[EntityMeta]:
        return dict(meta or {})

    def create_entity(
        self,
        start: int,
        end: int,
        meta: Optional[EntityMeta] = None
    ) -> Optional[MessageEntity]:
        if end <= start or self.entity_type is None:
            return None

        payload = self.from_markdown_meta(meta)
        if payload is None:
            return None

        return MessageEntity(
            type=self.entity_type,
            offset=start,
            length=end - start,
            **payload
        )

    @abstractmethod
    def render_html(self, content: str, entity: MessageEntity) -> str:
        raise NotImplementedError

    @abstractmethod
    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class SimpleTagKind:
    entity_type: enums.MessageEntityType
    html_tags: tuple[str, ...]
    html_tag: str
    markdown_token: str


class SimpleTagSpec(EntitySpec):
    def __init__(self, kind: SimpleTagKind) -> None:
        self.entity_type = kind.entity_type
        self.html_tags = kind.html_tags
        self._html_tag = kind.html_tag
        self._markdown_token = kind.markdown_token

    def render_html(self, content: str, entity: MessageEntity) -> str:
        return f"<{self._html_tag}>{content}</{self._html_tag}>"

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        return f"{self._markdown_token}{content}{self._markdown_token}"


class LinkSpec(EntitySpec):
    entity_type = enums.MessageEntityType.TEXT_LINK
    html_tags = ("a",)
    USER_LINK_RE = re.compile(r"^tg://user\?id=(\d+)$")

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        url = attrs.get("href")
        if not url:
            return None

        mention_match = self.USER_LINK_RE.fullmatch(url)
        if mention_match:
            return {
                "type": enums.MessageEntityType.TEXT_MENTION,
                "user": MentionUserRef(id=int(mention_match.group(1)))
            }

        return {"url": url}

    def from_markdown_meta(self, meta: Optional[EntityMeta] = None) -> Optional[EntityMeta]:
        payload = dict(meta or {})
        entity_type = payload.pop("type", None)

        if entity_type == enums.MessageEntityType.TEXT_MENTION:
            return None

        return payload

    def create_entity(
        self,
        start: int,
        end: int,
        meta: Optional[EntityMeta] = None
    ) -> Optional[MessageEntity]:
        if end <= start:
            return None

        payload = dict(meta or {})
        entity_type = payload.pop("type", self.entity_type)

        if entity_type is None:
            return None

        return MessageEntity(
            type=entity_type,
            offset=start,
            length=end - start,
            **payload
        )

    def render_html(self, content: str, entity: MessageEntity) -> str:
        url = html.escape(entity.url or "", quote=True)
        return f'<a href="{url}">{content}</a>'

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        return f"[{content}]({entity.url or ''})"


class TextMentionSpec(EntitySpec):
    entity_type = enums.MessageEntityType.TEXT_MENTION

    def render_html(self, content: str, entity: MessageEntity) -> str:
        if entity.user is None:
            return content

        return f'<a href="tg://user?id={entity.user.id}">{content}</a>'

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        if entity.user is None:
            return content

        return f"[{content}](tg://user?id={entity.user.id})"


class PreSpec(EntitySpec):
    entity_type = enums.MessageEntityType.PRE
    html_tags = ("pre",)

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        return {"language": attrs.get("language", "")}

    def render_html(self, content: str, entity: MessageEntity) -> str:
        if entity.language:
            language = html.escape(entity.language, quote=True)
            return f'<pre language="{language}">{content}</pre>'
        return f"<pre>{content}</pre>"

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        language = entity.language or ""
        return f"```{language}\n{content}\n```"


class BlockquoteSpec(EntitySpec):
    entity_type = enums.MessageEntityType.BLOCKQUOTE
    html_tags = ("blockquote",)

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        if "expandable" in attrs:
            return {"expandable": True}
        return {}

    def render_html(self, content: str, entity: MessageEntity) -> str:
        if entity.expandable:
            return f"<blockquote expandable>{content}</blockquote>"
        return f"<blockquote>{content}</blockquote>"

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        return "\n".join(
            ">" if line == "" else f"> {line}"
            for line in content.split("\n")
        )


class CustomEmojiSpec(EntitySpec):
    entity_type = enums.MessageEntityType.CUSTOM_EMOJI
    html_tags = ("tg-emoji", "emoji")

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        emoji_id = attrs.get("emoji-id") or attrs.get("id")
        if not emoji_id:
            return None

        try:
            return {"custom_emoji_id": int(emoji_id)}
        except ValueError:
            return None

    def render_html(self, content: str, entity: MessageEntity) -> str:
        emoji_id = html.escape(str(entity.custom_emoji_id), quote=True)
        return f'<tg-emoji emoji-id="{emoji_id}">{content}</tg-emoji>'

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        return f"![{content}](tg://emoji?id={entity.custom_emoji_id})"


class DateTimeSpec(EntitySpec):
    entity_type = enums.MessageEntityType.DATE_TIME
    html_tags = ("tg-time",)

    def from_html_attrs(self, attrs: Dict[str, str]) -> Optional[EntityMeta]:
        unix_time = attrs.get("unix")
        if not unix_time:
            return None

        try:
            payload: EntityMeta = {"unix_time": int(unix_time)}
        except ValueError:
            return None

        if "format" in attrs:
            payload["date_time_format"] = attrs["format"] or None

        return payload

    def render_html(self, content: str, entity: MessageEntity) -> str:
        attrs = [f'unix="{html.escape(str(entity.unix_time), quote=True)}"']
        if entity.date_time_format:
            attrs.append(f'format="{html.escape(entity.date_time_format, quote=True)}"')
        return f"<tg-time {' '.join(attrs)}>{content}</tg-time>"

    def render_markdown(self, content: str, entity: MessageEntity) -> str:
        target = f"tg://time?unix={entity.unix_time}"
        if entity.date_time_format:
            target += f"&format={entity.date_time_format}"
        return f"![{content}]({target})"


SIMPLE_TAG_KINDS = (
    SimpleTagKind(
        entity_type=enums.MessageEntityType.BOLD,
        html_tags=("b", "strong"),
        html_tag="b",
        markdown_token="**"
    ),
    SimpleTagKind(
        entity_type=enums.MessageEntityType.ITALIC,
        html_tags=("i", "em"),
        html_tag="i",
        markdown_token="__"
    ),
    SimpleTagKind(
        entity_type=enums.MessageEntityType.UNDERLINE,
        html_tags=("u", "ins"),
        html_tag="u",
        markdown_token="--"
    ),
    SimpleTagKind(
        entity_type=enums.MessageEntityType.STRIKETHROUGH,
        html_tags=("s", "strike", "del"),
        html_tag="s",
        markdown_token="~~"
    ),
    SimpleTagKind(
        entity_type=enums.MessageEntityType.SPOILER,
        html_tags=("spoiler", "tg-spoiler"),
        html_tag="spoiler",
        markdown_token="||"
    ),
    SimpleTagKind(
        entity_type=enums.MessageEntityType.CODE,
        html_tags=("code",),
        html_tag="code",
        markdown_token="`"
    ),
)


HTML_SPECS = (
    *(SimpleTagSpec(kind) for kind in SIMPLE_TAG_KINDS),
    LinkSpec(),
    TextMentionSpec(),
    PreSpec(),
    BlockquoteSpec(),
    CustomEmojiSpec(),
    DateTimeSpec(),
)

HTML_TAGS = {
    tag: spec
    for spec in HTML_SPECS
    for tag in spec.html_tags
}

ENTITY_SPECS = {
    spec.entity_type: spec
    for spec in HTML_SPECS
    if spec.entity_type is not None
}

HTML_ENTITY_ORDER = (
    enums.MessageEntityType.BOLD,
    enums.MessageEntityType.UNDERLINE,
    enums.MessageEntityType.ITALIC,
    enums.MessageEntityType.STRIKETHROUGH,
    enums.MessageEntityType.SPOILER,
    enums.MessageEntityType.TEXT_LINK,
    enums.MessageEntityType.CODE,
    enums.MessageEntityType.PRE,
    enums.MessageEntityType.BLOCKQUOTE,
    enums.MessageEntityType.CUSTOM_EMOJI,
    enums.MessageEntityType.DATE_TIME,
)

MARKDOWN_ENTITY_ORDER = (
    enums.MessageEntityType.BOLD,
    enums.MessageEntityType.ITALIC,
    enums.MessageEntityType.UNDERLINE,
    enums.MessageEntityType.STRIKETHROUGH,
    enums.MessageEntityType.SPOILER,
    enums.MessageEntityType.TEXT_LINK,
    enums.MessageEntityType.CUSTOM_EMOJI,
    enums.MessageEntityType.DATE_TIME,
    enums.MessageEntityType.CODE,
    enums.MessageEntityType.PRE,
    enums.MessageEntityType.BLOCKQUOTE,
)
