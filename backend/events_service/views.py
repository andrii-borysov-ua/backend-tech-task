from .models import Event
from .serializers import EventSerializer
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@swagger_auto_schema(method='post', request_body=EventSerializer(many=True), responses={201: "Events ingested successfully", 400: "Validation errors"})
@api_view(['POST'])
def ingest_events(request):
    if not isinstance(request.data, list):
        return Response({"error": "Expected a list of events"}, status=status.HTTP_400_BAD_REQUEST)
    created_count = 0
    with transaction.atomic():
        for event_data in request.data:
            serializer = EventSerializer(data=event_data)
            if serializer.is_valid():
                event, created = Event.objects.get_or_create(event_id=serializer.validated_data['event_id'], defaults=serializer.validated_data)
                if created:
                    created_count += 1
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({"processed": len(request.data), "created": created_count}, status=status.HTTP_201_CREATED)

