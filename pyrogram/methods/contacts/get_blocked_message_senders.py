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

from typing import AsyncGenerator

import pyrogram
from pyrogram import enums, raw, types


class GetBlockedMessageSenders:
    async def get_blocked_message_senders(
        self: "pyrogram.Client",
        block_list: "enums.BlockList" = enums.BlockList.MAIN,
        offset: int = 0,
        limit: int = 0,
    ) -> AsyncGenerator["types.Chat"]:
        """Returns users and chats that were blocked by the current user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            block_list (``pyrogram.enums.BlockList``, *optional*):
                The block list from which to return users.

            offset (``int``, *optional*):
                Number of users and chats to skip in the result, must be non-negative.

            limit (``int``, *optional*):
                The maximum number of users and chats to return.

        Returns:
            AsyncGenerator of :obj:`~pyrogram.types.Chat`: An async generator that yields Chat objects.

        Example:
            .. code-block:: python
                async for chat in app.get_blocked_message_senders():
                    print(chat)
        """

        total = abs(limit) or (1 << 31) - 1
        limit = min(100, total)

        r = await self.invoke(
            raw.functions.contacts.GetBlocked(
                offset=offset,
                limit=limit,
                my_stories_from=block_list == enums.BlockList.STORIES,
            )
        )

        users = {i.id: i for i in r.users}
        chats = {i.id: i for i in r.chats}

        for peer in r.blocked:
            if isinstance(peer.peer_id, raw.types.PeerUser):
                yield types.User._parse(self, users[peer.peer_id.user_id])
            elif isinstance(peer.peer_id, raw.types.PeerChat):
                yield types.Chat._parse(self, chats[peer.peer_id.chat_id])
            elif isinstance(peer.peer_id, raw.types.PeerChannel):
                yield types.Chat._parse(self, chats[peer.peer_id.channel_id])
