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

from typing import Union
import pyrogram
from pyrogram import raw

class CancelStarSubscription:
    async def cancel_star_subscription(
        self: "pyrogram.Client",
        user_id: Union[int, str],
        charge_id: str,
        restore: bool = False
    ) -> bool:
        """
        Cancel a Telegram Stars subscription for a user.

        Parameters:
            user_id (``int`` | ``pyrogram.types.InputUser``):
                The user whose subscription will be cancelled. Can be a user ID or an InputUser object.

            charge_id (``str``):
                The unique identifier of the payment charge to cancel.

            restore (``bool``, *optional*):
                If True, the subscription will be restored instead of cancelled. Defaults to False.

        Returns:
            ``bool``: True on success, False otherwise.
        """
        return await self.invoke(
            raw.functions.payments.BotCancelStarsSubscription(
                user_id=await self.resolve_peer(user_id),
                charge_id=charge_id,
                restore=restore
            )
        )
