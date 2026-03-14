from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypedDict

from pyrogram.types.list import List as TypesList
from pyrogram.types.messages_and_media.message_entity import MessageEntity

EntityMeta = Dict[str, Any]


class ParseResult(TypedDict):
    message: str
    entities: Optional[TypesList]


@dataclass
class EntityNode:
    entity: Optional[MessageEntity]
    start: int
    end: int
    children: List["EntityNode"] = field(default_factory=list)


@dataclass(frozen=True)
class MentionUserRef:
    id: int
