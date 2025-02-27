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

from typing import List, Optional

import pyrogram
from pyrogram import raw, types

class GetStoryViews:
    async def get_story_views(
        self: "pyrogram.Client",
        story_id: int,
        limit: int = 0,
        contacts_only: bool = None,
        reactions_first: bool = None,
        query: str = None
    ) -> Optional[List["types.User"]]:
        """Get story views

        Parameters:
            story_id (``int``):
                Pass a story identifier to get the story views.

            limit (``int``, *optional*):
                Maximum number of views to return.

            contacts_only (``bool``, *optional*):
                Only Get views made by your contacts, Defaults to False.

            reactions_first (``bool``, *optional*):
                If True, return reactions first, Defaults to False.

            query (``str``, *optional*):
                Search for specific users.
        
        Returns:
            :obj: List of :obj:`~pyrogram.types.User`.
        
        Example:
            .. code-block:: python

                # Get views
                users = await app.get_story_views(3)

                for user in users:
                    print(user)
        """

        r = await self.invoke(
            raw.functions.stories.get_story_views_list.GetStoryViewsList(
                peer=raw.types.InputPeerSelf(),
                id=story_id,
                offset="None",
                limit=limit,
                just_contacts=contacts_only,
                reactions_first=reactions_first,
                forwards_first=None,
                q=query
            )
        )

        users = types.List()

        for i in r.users:
            users.append(types.User._parse(self, i))
        
        return users