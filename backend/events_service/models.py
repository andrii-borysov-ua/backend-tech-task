from django.db import models
from django.db.models import JSONField

class Event(models.Model):
    event_id = models.UUIDField(primary_key=True, editable=False)
    occurred_at = models.DateTimeField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    properties = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'events'
        indexes = [
            models.Index(fields=['occurred_at', 'user_id']),
            models.Index(fields=['event_type', 'occurred_at']),
        ]

    def __str__(self):
        return f"Event {self.event_type} by {self.user_id} at {self.occurred_at}"

