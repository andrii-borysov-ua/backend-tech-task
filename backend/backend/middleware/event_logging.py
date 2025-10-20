import os
import logging
import time
from threading import Lock


logger = logging.getLogger('events_service')


class EventLoadMiddleware:
    FLAG_FILE = '/logs/event_logging_flag'  # Create "event_logging_flag" file to start logging
    CHECK_INTERVAL = 3600

    def __init__(self, get_response):
        self.get_response = get_response
        self.lock = Lock()
        self.count = 0
        self.start_time = time.time()
        self.last_flag_check = 0
        self.flag_enabled = False

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/api/events'):
            with self.lock:
                self.count += 1
                now = time.time()

                if now - self.last_flag_check > self.CHECK_INTERVAL:
                    self.flag_enabled = os.path.exists(self.FLAG_FILE)
                    self.last_flag_check = now

                elapsed = now - self.start_time
                if elapsed >= 60 and self.flag_enabled:
                    rate = self.count / elapsed
                    logger.info(f"Event ingest load: {self.count} events in {elapsed:.2f}s ({rate:.2f} per sec)")
                    self.count = 0
                    self.start_time = now
        return response
