import time
import threading
import random

class MsgId(int):
    _lock = threading.Lock()
    _last_time = 0
    _offset = 0

    def __new__(cls):
        with cls._lock:
            now = int(time.time())

            # Add a small random number to reduce collisions
            rand_shift = random.randint(1, 999)

            if now == cls._last_time:
                cls._offset = (cls._offset + rand_shift) & 0xFFFFFFFF
            else:
                cls._offset = rand_shift  # not 0 to avoid repeat on new second

            cls._last_time = now
            msg_id = (now << 32) | cls._offset

        return int.__new__(cls, msg_id & ((1 << 63) - 1))
