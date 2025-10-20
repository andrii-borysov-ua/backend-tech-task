from django.conf import settings
from django.http import JsonResponse
from events_service.utils.token_bucket import TokenBucket
import logging


logger = logging.getLogger('rate_limit')
buckets = {}


class RateLimitMiddleware:
    RATE = settings.RATE_LIMIT_RATE
    CAPACITY = settings.RATE_LIMIT_CAPACITY

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR', '')
        bucket = buckets.setdefault(ip, TokenBucket(self.RATE, self.CAPACITY))
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return JsonResponse({"detail": "Request limit exceeded"}, status=429)
        return self.get_response(request)
