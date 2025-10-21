from celery import shared_task
from .models import Event
from .serializers import EventSerializer
from django.db import transaction
import logging


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_event_batch(self, validated_events):
    created_count = 0
    skipped_count = 0
    with transaction.atomic():
        for data in validated_events:
            event, created = Event.objects.get_or_create(event_id=data['event_id'], defaults=data)
            if created:
                created_count += 1
            else:
                skipped_count += 1
    logger.info(f"processed: {len(validated_events)}, created: {created_count}, skipped: {skipped_count}")
