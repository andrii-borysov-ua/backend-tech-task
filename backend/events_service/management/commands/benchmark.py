import time
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from events_service.models import Event

class Command(BaseCommand):
    help = 'Benchmark: insert 100k events and calculate DAU'

    def handle(self, *args, **kwargs):
        events = []
        base_time = timezone.now()
        for i in range(100_000):
            event = Event(
                event_id=str(uuid.uuid4()),
                occurred_at=base_time,
                user_id=i % 30000,
                event_type='login',
                properties={"session_id": "session_id", "country": "UA"}
            )
            if i % 4 == 0:
                base_time = base_time - timedelta(seconds=1)
            events.append(event)

        Event.objects.all().delete()

        start_time = time.time()
        Event.objects.bulk_create(events, batch_size=5000)
        insert_time = time.time() - start_time
        print(f'Inserted 100k events in {insert_time:.2f} seconds')

        start_time = time.time()
        dau = (Event.objects.filter(occurred_at__gte=base_time - timedelta(days=1)).values('user_id').distinct().count())
        query_time = time.time() - start_time
        print(f'DAU count: {dau} calculated in {query_time:.2f} seconds')
