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

import logging
from typing import Optional, Union
import re
import pyrogram
from pyrogram import raw, types, utils

log = logging.getLogger(__name__)

class GetMessage:
    async def get_message(
        self: "pyrogram.Client",
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[Union[int, str]] = None,
        reply: Optional[bool] = None,
        replies: int = 1
    ) -> "types.Message":
        """Get a single message from a chat by using a message identifier or link.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``, *optional*):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            message_id (``int`` | ``str``, *optional*):
                Pass a single message identifier or a link to get the content of the message itself
                or the previous message you replied to using this message.

            reply (``bool``, *optional*):
                If True, you will get the content of the previous message you replied to using this message.

            replies (``int``, *optional*):
                The number of subsequent replies to get for the message.
                Pass 0 for no reply at all or -1 for unlimited replies.
                Defaults to 1.

        Returns:
            :obj:`~pyrogram.types.Message`: A single message is returned.

        Example:
            .. code-block:: python

                # Get one message
                await app.get_message(chat_id=chat_id, message_id=12345)

                # Get message by ignoring any replied-to message
                await app.get_message(chat_id=chat_id, message_id=12345, replies=0)

                # Get message with all chained replied-to messages
                await app.get_message(chat_id=chat_id, message_id=12345, replies=-1)

                # Get the replied-to message of a message
                await app.get_message(chat_id=chat_id, message_id=12345, reply=True)

                # Get message from link
                await app.get_message(message_id="https://t.me/pyrogram/49")

        Raises:
            ValueError: In case of invalid arguments or if the message does not exist.
        """
        _type = raw.types.InputMessageReplyTo if reply else raw.types.InputMessageID

        if isinstance(message_id, str):
            match = re.match(r"^(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.(?:org|me|dog)/(?:c/)?)([\w]+)(?:/\d+)*/(\d+)/?$", message_id.lower())

            if match:
                try:
                    chat_id = utils.get_channel_id(int(match.group(1)))
                except ValueError:
                    chat_id = match.group(1)

                ids = [_type(id=int(match.group(2)))]
            else:
                raise ValueError("Invalid message link.")
        else:
            if not chat_id:
                raise ValueError("Invalid chat_id.")

            if message_id is None:
                raise ValueError("Invalid message_id.")

            ids = [_type(id=message_id)]

        peer = await self.resolve_peer(chat_id)

        if replies < 0:
            replies = (1 << 31) - 1

        if isinstance(peer, raw.types.InputPeerChannel):
            rpc = raw.functions.channels.GetMessages(channel=peer, id=ids)
        else:
            rpc = raw.functions.messages.GetMessages(id=ids)

        r = await self.invoke(rpc, sleep_threshold=-1)

        messages = await utils.parse_messages(self, r, replies=replies)

        if messages:
            return messages[0]

        msg = "Message does not exist"
        raise ValueError(msg)