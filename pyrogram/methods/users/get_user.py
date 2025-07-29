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

import asyncio
from typing import Union

import pyrogram
from pyrogram import raw
from pyrogram import types


class GetUser:
    async def get_user(
        self: "pyrogram.Client",
        user_id: Union[int, str]
    ) -> "types.User":
        """Get information about a single user.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            user_id (``int`` | ``str``):
                A single user identifier (id or username).
                For a contact that exists in your Telegram address book you can use his phone number (str).

        Returns:
            :obj:`~pyrogram.types.User`: A single user is returned.

        Example:
            .. code-block:: python

                # Get information about one user
                await app.get_user("me")

                # Get information by user ID
                await app.get_user(12345)

                # Get information by username
                await app.get_user("@username")

        Raises:
            ValueError: In case of invalid arguments or if the user does not exist.
        """
        peer = await self.resolve_peer(user_id)

        r = await self.invoke(
            raw.functions.users.GetUsers(
                id=[peer]
            )
        )

        users = types.List()

        for i in r:
            users.append(types.User._parse(self, i))

        if users:
            return users[0]

        msg = "User does not exist"
        raise ValueError(msg)