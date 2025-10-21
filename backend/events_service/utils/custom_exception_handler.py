from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception(f"Internal server error: {exc}")
        _response = Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 400:
        logger.warning(f"Validation error: {response.data} in view {context.get('view')}")
        _response = Response({"error": response.data}, status=response.status_code)
    return None
