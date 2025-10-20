import time
from threading import Lock


class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.timestamp = time.time()
        self.lock = Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.time()
            elapsed = now - self.timestamp
            self.timestamp = now
            self.tokens += elapsed * self.rate
            if self.tokens > self.capacity:
                self.tokens = self.capacity
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
