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

from typing import Callable

from .handler import Handler


class ErrorHandler(Handler):
    """The Error handler class. Used to handle update errors. It is intended to be used with
    :meth:`~pyrogram.Client.add_handler`

    For a nicer way to register this handler, have a look at the
    :meth:`~pyrogram.Client.on_error` decorator.

    Parameters:
        callback (``Callable``):
            Pass a function that will be called when an update handler raises an exception. It takes *(exc)*, *(handler)*, *(client)*
            as positional arguments (look at the section below for a detailed description).

    Other parameters:
        exc (:obj:`Exception`):
            The Exception object which was raised.
        handler (:obj:`~pyrogram.handlers.handler.Handler`):
            The handler whose callback raised this exception.
        client (:obj:`~pyrogram.Client`):
            The Client itself.
    """

    def __init__(self, callback: Callable):
        super().__init__(callback)
