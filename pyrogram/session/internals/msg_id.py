import time
import threading

class MsgId(int):
    _lock = threading.Lock()
    _last_time = 0
    _offset = 0

    def __new__(cls):
        with cls._lock:
            now = int(time.time())

            if now == cls._last_time:
                cls._offset = (cls._offset + 4) & 0xFFFFFFFF  # wrap if needed
            else:
                cls._offset = 0

            cls._last_time = now
            msg_id = (now << 32) | cls._offset

        return int.__new__(cls, msg_id & ((1 << 63) - 1))
