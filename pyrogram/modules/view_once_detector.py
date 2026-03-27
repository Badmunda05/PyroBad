# ✅ Correct and updated view_once_detector.py
from pyrogram.types import Message

async def is_view_once(message: Message) -> bool:
    """
    Detect if the message contains *true* view-once media.
    True view-once media usually has `ttl_seconds` <= 2.
    """
    media = (
        message.photo or 
        message.video or 
        message.document
    )
    if not media:
        return False

    ttl = getattr(media, "ttl_seconds", None)

    # Only treat as view-once if ttl_seconds exists and is 1 or 2
    return isinstance(ttl, int) and ttl <= 2
