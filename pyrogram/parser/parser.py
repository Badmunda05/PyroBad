#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import List, Optional

import pyrogram
from pyrogram import enums
from pyrogram.types.messages_and_media.message_entity import MessageEntity

from .combined import CombinedParser
from .html import HTML
from .markdown import Markdown
from .types import ParseResult


class Parser:
    def __init__(self, client: Optional["pyrogram.Client"]):
        self.client = client
        self.combined = CombinedParser(client)
        self.html = HTML(client)
        self.markdown = Markdown(client)

    async def parse(self, text: str, mode: Optional[enums.ParseMode] = None) -> ParseResult:
        text = str(text or "").strip()

        if mode is None:
            mode = self.client.parse_mode if self.client else enums.ParseMode.DEFAULT

        if mode == enums.ParseMode.DEFAULT:
            return await self.combined.parse(text)

        if mode == enums.ParseMode.MARKDOWN:
            return await self.markdown.parse(text)

        if mode == enums.ParseMode.HTML:
            return await self.html.parse(text)

        if mode == enums.ParseMode.DISABLED:
            return {"message": text, "entities": None}

        raise ValueError(f'Invalid parse mode "{mode}"')

    @staticmethod
    def unparse(text: str, entities: List[MessageEntity], is_html: bool) -> str:
        if is_html:
            return HTML.unparse(text, entities)
        return Markdown.unparse(text, entities)
