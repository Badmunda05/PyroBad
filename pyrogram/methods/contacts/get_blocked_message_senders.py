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
        block_list: enums.BlockList = enums.BlockList.MAIN,
        offset: int = 0,
        limit: int = 0,
    ) -> AsyncGenerator["types.User", None]:
        """Returns users and chats that were blocked by the current user.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            block_list (``pyrogram.enums.BlockList``, *optional*):
                The block list from which to return users.

            offset (``int``, *optional*):
                Number of users and chats to skip in the result; must be non-negative.

            limit (``int``, *optional*):
                The maximum number of users and chats to return; up to 100.

        Returns:
            AsyncGenerator of :obj:`~pyrogram.types.User`: An async generator that yields User objects.

        Example:
            .. code-block:: python
                async for user in app.get_blocked_message_senders():
                    print(user)
        """
        r = await self.invoke(
            raw.functions.contacts.GetBlocked(
                offset=offset,
                limit=limit,
                my_stories_from=True
                if block_list == enums.BlockList.STORIES
                else False,
            )
        )

        users = {i.id: i for i in r.users}
        chats = {i.id: i for i in r.chats}

        for peer in r.blocked:
            if isinstance(peer, raw.types.PeerUser) and peer.user_id in users:
                yield types.User._parse(self, users[peer.user_id])
            elif isinstance(peer, raw.types.PeerChat) and peer.chat_id in chats:
                yield types.Chat._parse(self, chats[peer.chat_id])
