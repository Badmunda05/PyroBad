from __future__ import annotations

import html
from html.parser import HTMLParser
from typing import Dict, List, Optional, TypedDict

import pyrogram
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .rendering import html_entity_rank, make_entity_list, render_entities
from .specs import EntitySpec, HTML_TAGS
from .types import EntityMeta, ParseResult
from .utils import add_surrogates, remove_surrogates


class _HTMLFrame(TypedDict):
    tag: str
    spec: EntitySpec
    start: int
    meta: EntityMeta


class _HTMLToEntitiesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.output: List[str] = []
        self.entities: List[MessageEntity] = []
        self.stack: List[_HTMLFrame] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        spec, payload = self._resolve_spec(tag, attrs)

        if spec is None:
            self.output.append(self.get_starttag_text())
            return

        if tag == "code" and self.stack and self.stack[-1]["tag"] == "pre":
            language = self._extract_language(dict(attrs))
            if language:
                self.stack[-1]["meta"]["language"] = language
            return

        self.stack.append(
            {
                "tag": tag,
                "spec": spec,
                "start": len("".join(self.output)),
                "meta": payload,
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if tag == "code" and self.stack and self.stack[-1]["tag"] == "pre":
            return

        index = self._find_frame(tag)
        if index is None:
            self.output.append(f"</{tag}>")
            return

        frame = self.stack.pop(index)
        entity = frame["spec"].create_entity(frame["start"], len("".join(self.output)), frame["meta"])
        if entity is not None:
            self.entities.append(entity)

    def handle_startendtag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        self.output.append(add_surrogates(data))

    def handle_entityref(self, name: str) -> None:
        self.output.append(add_surrogates(html.unescape(f"&{name};")))

    def handle_charref(self, name: str) -> None:
        self.output.append(add_surrogates(html.unescape(f"&#{name};")))

    def handle_comment(self, data: str) -> None:
        return

    def parse(self, text: str) -> ParseResult:
        self.feed(text)
        self.close()

        while self.stack:
            frame = self.stack.pop()
            self.output.insert(frame["start"], self._rebuild_start_tag(frame["tag"], frame["meta"]))

        message = remove_surrogates("".join(self.output))
        self.entities.sort(key=lambda entity: (entity.offset, entity.length))

        return {
            "message": message,
            "entities": make_entity_list(self.entities)
        }

    def _resolve_spec(
        self,
        tag: str,
        attrs: List[tuple[str, Optional[str]]]
    ) -> tuple[Optional[EntitySpec], Optional[EntityMeta]]:
        attrs_map = self._attrs_to_dict(attrs)
        spec = HTML_TAGS.get(tag)

        if tag == "span" and attrs_map.get("class") == "tg-spoiler":
            spec = HTML_TAGS.get("tg-spoiler")

        if spec is None:
            return None, None

        payload = spec.from_html_attrs(attrs_map)
        if payload is None:
            return None, None

        return spec, payload

    @staticmethod
    def _attrs_to_dict(attrs: List[tuple[str, Optional[str]]]) -> Dict[str, str]:
        result = {}

        for key, value in attrs:
            result[key] = "" if value is None else value

        return result

    @staticmethod
    def _extract_language(attrs: Dict[str, str]) -> Optional[str]:
        value = attrs.get("class", "")

        for item in value.split():
            if item.startswith("language-") and len(item) > 9:
                return item[9:]

        return None

    def _find_frame(self, tag: str) -> Optional[int]:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                return index

        return None

    @staticmethod
    def _rebuild_start_tag(tag: str, meta: EntityMeta) -> str:
        if tag == "a" and meta.get("url"):
            return f'<a href="{meta["url"]}">'
        if tag == "pre" and meta.get("language"):
            return f'<pre language="{meta["language"]}">'
        if tag == "blockquote" and meta.get("expandable"):
            return "<blockquote expandable>"
        if tag == "tg-emoji" and meta.get("custom_emoji_id"):
            return f'<tg-emoji emoji-id="{meta["custom_emoji_id"]}">'
        return f"<{tag}>"


class HTML:
    def __init__(self, client: Optional["pyrogram.Client"]) -> None:
        self.client = client

    async def parse(self, text: str) -> ParseResult:
        return _HTMLToEntitiesParser().parse(text)

    @staticmethod
    def unparse(text: str, entities: List[MessageEntity]) -> str:
        if not entities:
            return text

        return render_entities(
            text=text,
            entities=entities,
            formatter=lambda spec, content, entity: spec.render_html(content, entity),
            rank_getter=html_entity_rank,
            escape_text=lambda value: html.escape(remove_surrogates(value), quote=False)
        )
