from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField()
    occurred_at = serializers.DateTimeField()
    user_id = serializers.IntegerField(min_value=1)
    event_type = serializers.CharField(max_length=100)
    properties = serializers.JSONField()

    class Meta:
        model = Event
        fields = ['event_id', 'occurred_at', 'user_id', 'event_type', 'properties']

    def validate_event_type(self, value):
        allowed_types = {"add_to_cart", "app_open", "login", "logout", "message_sent", "purchase", "view_item"}
        if value not in allowed_types:
            raise serializers.ValidationError(f"'event_type' must be one of {allowed_types}")
        return value

    def validate_properties(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("'properties' must be a dictionary")
        if "country" not in value:
            raise serializers.ValidationError("'properties' must include 'country' field")
        if "session_id" not in value:
            raise serializers.ValidationError("'properties' must include 'session_id' field")
        return value