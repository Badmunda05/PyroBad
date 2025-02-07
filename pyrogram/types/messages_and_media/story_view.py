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

import pyrogram
from pyrogram import raw, types
from datetime import datetime

from ..object import Object
from ..update import Update


class StoryView(Object, Update):
    """Story view date and reaction information.

    Parameters:
        user_id (``int``):
            The user that viewed the story.
        
        date (:obj:`~datetime`):
            When did the user view the story.
        
        message (:obj:`~pyrogram.types.Message`):
            The message with the forwarded story.
        
        peer_id (:obj:`~Peer`):
            The peer that reposted the story.

        story (:obj:`~StoryItem`):
            The reposted story.

        blocked (``bool``, *optional*):
            Whether we have completely blocked this user, including from viewing more of our stories.
        
        blocked_my_stories_from (``bool``, *optional*):
            Whether we have blocked this user from viewing more of our stories.
        
        reaction (:obj:`~pyrogram.types.Reaction`, *optional*):
            If present, contains the reaction that the user left on the story.
    """

    def __init__(
        self,
        *,
        client: "pyrogram.Client" = None,
        user_id: int = None,
        date: int = None,
        message: "types.Message" = None,
        peer_id: "raw.base.Peer" = None,
        story: "raw.base.StoryItem" = None,
        blocked: bool = None,
        blocked_my_stories_from: bool = None,
        reaction: "types.Reaction" = None
    ):
        super().__init__(client)

        self.user_id = user_id
        self.date = date
        self.message = message
        self.peer_id = peer_id
        self.story = story
        self.blocked = blocked
        self.blocked_my_stories_from = blocked_my_stories_from
        self.reaction = reaction
    
    @staticmethod
    async def _parse(
        client: "pyrogram.Client",
        storyview: "raw.base.StoryView",
    ) -> "StoryView":
        if isinstance(storyview, raw.types.StoryView):
            return StoryView(
                client=client,
                user_id=storyview.user_id,
                date=datetime.fromtimestamp(storyview.date),
                blocked=storyview.blocked,
                blocked_my_stories_from=storyview.blocked_my_stories_from,
                reaction=types.Reaction._parse(client, storyview.reaction)
            )
        
        if isinstance(storyview, raw.types.StoryViewPublicForward):
            return StoryView(
                client=client,
                message=storyview.message,
                blocked=storyview.blocked,
                blocked_my_stories_from=storyview.blocked_my_stories_from
            )
        
        if isinstance(storyview, raw.types.StoryViewPublicRepost):
            return StoryView(
                client=client,
                peer_id=storyview.peer_id,
                story=storyview.story,
                blocked=storyview.blocked,
                blocked_my_stories_from=storyview.blocked_my_stories_from
            )
