import csv
import json
from backend.events_service.models import Event
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Path to CSV with historic data')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file_path']
        imported_count = 0
        skipped_count = 0
        error_count = 0
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            with transaction.atomic():
                for row in reader:
                    try:
                        event_id = row['event_id']
                        occurred_at = parse_datetime(row['occurred_at'])
                        user_id = int(row['user_id'])
                        event_type = row['event_type']
                        properties = json.loads(row['properties_json']) if row['properties_json'] else {}
                        event, created = Event.objects.get_or_create(
                            event_id=event_id,
                            defaults={'occurred_at': occurred_at, 'user_id': user_id, 'event_type': event_type, 'properties': properties}
                        )
                        if created:
                            self.stdout.write(f'Added event {event_id}')
                            imported_count += 1
                        else:
                            self.stdout.write(f'Event {event_id} already exists, skipped')
                            skipped_count += 1
                    except Exception as e:
                        self.stderr.write(f'Error processing row {row}: {e}')
                        error_count += 1
                        continue

        self.stdout.write(self.style.SUCCESS(f'Import finished. Imported {imported_count}, skipped {skipped_count}, with errors: {error_count}'))
