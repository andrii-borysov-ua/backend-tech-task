from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField()
    occurred_at = serializers.DateTimeField()
    user_id = serializers.CharField(max_length=255)
    event_type = serializers.CharField(max_length=100)
    properties = serializers.JSONField()

    class Meta:
        model = Event
        fields = ['event_id', 'occurred_at', 'user_id', 'event_type', 'properties']
