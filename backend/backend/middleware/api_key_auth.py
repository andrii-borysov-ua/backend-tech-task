from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):

    def authenticate(self, request):
        api_key = request.headers.get('X-Api-Key')
        correct_key = settings.ACCESS_API_KEY
        if not api_key: raise AuthenticationFailed("API Key is missing.")
        if api_key != correct_key: raise AuthenticationFailed("Invalid API Key.")
        return (None, None)
