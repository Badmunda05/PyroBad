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

from datetime import datetime
from typing import AsyncIterator, Union, List

import pyrogram
from pyrogram import raw, types, utils


async def get_chunk(
    *,
    client: "pyrogram.Client",
    chat_id: Union[int, str],
    limit: int = 0,
    offset: int = 0,
    from_message_id: int = 0,
    from_date: datetime = utils.zero_datetime(),
    min_id: int = 0,
    max_id: int = 0,
    reverse: bool = False,
) -> List[types.Message]:
    """
    Get chunk of messages from chat history.

    :param client: Pyrogram client instance.
    :param chat_id: Chat identifier.
    :param limit: Maximum number of messages to retrieve.
    :param offset: Offset for pagination.
    :param from_message_id: Starting message ID.
    :param from_date: Starting date.
    :param min_id: Minimum message ID (inclusive).
    :param max_id: Maximum message ID (inclusive).
    :param reverse: If True, retrieve messages from oldest to newest.
    :returns: List of messages.
    """
    # Telegram API requires `offset_id` as starting point, boundaries alone don't work
    api_from_message_id: int = from_message_id
    api_min_id: int = min_id
    api_max_id: int = max_id
    api_offset: int = offset

    # Telegram API works backwards from `offset_id`, so we need proper starting points
    # when only boundaries are provided without explicit starting message ID
    if (min_id or max_id) and not from_message_id:
        if max_id:
            # Start from `max_id`+1 to include max_id in results (API uses exclusive upper bound)
            api_from_message_id = max_id + 1
        elif min_id:
            # Start from latest messages (0 means latest) and let `min_id` filter from below
            api_from_message_id = 0

    # When both boundaries are set, always start from the upper boundary for efficiency
    if min_id and max_id and not from_message_id:
        api_from_message_id = max_id + 1

    messages: raw.base.messages.Messages = await client.invoke(
        raw.functions.messages.GetHistory(
            peer=await client.resolve_peer(chat_id),  # type: ignore[arg-type]
            offset_id=api_from_message_id,
            offset_date=int(from_date.timestamp()),
            add_offset=api_offset,
            limit=limit,
            max_id=api_max_id,
            min_id=api_min_id,
            hash=0,
        ),
        sleep_threshold=60,
    )

    parsed_messages = await utils.parse_messages(client, messages, replies=0)

    # Telegram API returns messages in descending order by default (newest first)
    if reverse:
        # Make sure the order is ascending (oldest first)
        parsed_messages.reverse()
    return parsed_messages


class GetChatHistory:
    async def get_chat_history(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        limit: int = 0,
        offset: int = 0,
        offset_id: int = 0,
        offset_date: datetime = utils.zero_datetime(),
        min_id: int = 0,
        max_id: int = 0,
        reverse: bool = False,
    ) -> AsyncIterator[types.Message]:
        """Get messages from a chat history.

        The messages are returned in reverse chronological order.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            limit (``int``, *optional*):
                Limits the number of messages to be retrieved.
                By default, no limit is applied and all messages are returned.

            offset (``int``, *optional*):
                Sequential number of the first message to be returned.
                Negative values are also accepted and become useful in case you set offset_id or offset_date.

            offset_id (``int``, *optional*):
                Identifier of the first message to be returned.
                Note: This parameter is deprecated and should not be used. Use min_id/max_id instead for proper filtering.

            offset_date (:py:obj:`~datetime.datetime`, *optional*):
                Pass a date as offset to retrieve only older messages starting from that date.

            min_id (``int``, *optional*):
                If a positive value was provided, the method will return only messages with IDs more than or equal to min_id (inclusive).

            max_id (``int``, *optional*):
                If a positive value was provided, the method will return only messages with IDs less than or equal to max_id (inclusive).

            reverse (``bool``, *optional*):
                Pass True to retrieve the messages from oldest to newest.

        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.

        Example:
            .. code-block:: python

                async for message in app.get_chat_history(chat_id):
                    print(message.text)
        """
        current: int = 0
        total: int = limit or (1 << 31) - 1
        chunk_limit: int = min(100, total)

        # Telegram API requires different parameter setup for reverse vs normal iteration
        # because `GetHistory` always returns messages in descending order by default
        if reverse:
            # For reverse (oldest to newest): start from `min_id` and work upward
            from_message_id: int = min_id if min_id else 1
            # Adjust boundaries to make them inclusive: API treats boundaries as exclusive
            api_min_id: int = (min_id - 1) if min_id else 0
            api_max_id: int = (max_id + 1) if max_id else 0
            # Negative offset moves the starting point backwards, required for reverse iteration
            current_offset: int = offset - chunk_limit
        else:
            # For normal (newest to oldest): start from `max_id` and work downward
            from_message_id = max_id if max_id else 0
            # Adjust boundaries to make them inclusive: API treats boundaries as exclusive
            api_min_id = (min_id - 1) if min_id else 0
            api_max_id = (max_id + 1) if max_id else 0
            current_offset = offset

        while current < total:
            remaining: int = total - current
            current_chunk_limit: int = min(chunk_limit, remaining)

            messages = await get_chunk(
                client=self,
                chat_id=chat_id,
                limit=current_chunk_limit,
                offset=current_offset,
                from_message_id=from_message_id,
                from_date=offset_date,
                min_id=api_min_id,
                max_id=api_max_id,
                reverse=reverse,
            )

            # If no messages were returned, we can stop iterating
            if not messages:
                break

            # Yield messages
            for message in messages:
                yield message
                current += 1

            # Update pagination parameters for next chunk iteration
            if reverse:
                # For reverse: continue from next message after the last one we processed
                from_message_id = messages[-1].id + 1
            else:
                # For normal: continue from the last message ID we processed
                from_message_id = messages[-1].id
