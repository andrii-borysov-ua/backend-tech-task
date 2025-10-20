import logging
import time


logger = logging.getLogger('requests')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = (time.time() - start_time) * 1000
        logger.info(f"{request.method} {request.get_full_path()} completed in {duration:.2f} ms with status {response.status_code}")
        return response
