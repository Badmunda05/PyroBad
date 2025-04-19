import time
import os
import threading

class MsgId:
    # Process-unique 10-bit random node ID (or thread ID hashed)
    _node_id = os.getpid() & 0x3FF  # max 1023
    _last_ns = 0
    _sequence = 0

    @classmethod
    def __new__(cls) -> int:
        now_ns = time.time_ns()
        timestamp = now_ns // 1_000_000  # convert to ms

        if now_ns == cls._last_ns:
            cls._sequence = (cls._sequence + 1) & 0xFFF  # 12-bit sequence
            if cls._sequence == 0:
                # spin until next nanosecond
                while time.time_ns() <= now_ns:
                    pass
                timestamp = time.time_ns() // 1_000_000
        else:
            cls._sequence = 0

        cls._last_ns = now_ns

        # 41-bit timestamp | 10-bit node_id | 12-bit sequence = 63 bits
        msg_id = ((timestamp & ((1 << 41) - 1)) << 22) | (cls._node_id << 12) | cls._sequence
        return int(msg_id & ((1 << 63) - 1))  # Force 63-bit signed int
