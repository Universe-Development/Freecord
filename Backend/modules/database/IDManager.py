import time
import threading
from modules.database.Database import singleton

@singleton
class SnowflakeIDGenerator:
    def __init__(self, epoch=1609459200000):
        self.epoch = epoch
        self.sequence = 0
        self.last_timestamp = -1

        self.sequence_bits = 12

        self.max_sequence = -1 ^ (-1 << self.sequence_bits)

        self.timestamp_shift = self.sequence_bits

        self.lock = threading.Lock()

    def _current_timestamp(self):
        return int(time.time() * 1000)

    def _wait_for_next_millis(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID.")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self._wait_for_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id_ = ((timestamp - self.epoch) << self.timestamp_shift) | \
                  self.sequence

            return id_
