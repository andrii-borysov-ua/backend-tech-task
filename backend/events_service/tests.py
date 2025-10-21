import uuid
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from events_service.models import Event
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


class EventIngestTests(APITestCase):
    def setUp(self):
        self.url_import = reverse('ingest_events')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_create_event(self):
        data = [{
            "event_id": str(uuid.uuid4()),
            "occurred_at": timezone.now().isoformat(),
            "user_id": 1,
            "event_type": "login",
            "properties": {"country": "PL", "session_id": "5ef18783"}
        }, ]
        response = self.client.post(self.url_import, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Event.objects.get().user_id, 1)

    def test_idempotency_of_import(self):
        data = [{
            "event_id": str(uuid.uuid4()),
            "occurred_at": timezone.now().isoformat(),
            "user_id": 1,
            "event_type": "login",
            "properties": {"country": "UK", "session_id": "587e644d", "method": "apple"}
        }, ]
        response1 = self.client.post(self.url_import, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_202_ACCEPTED)
        count_after_first = Event.objects.count()
        response2 = self.client.post(self.url_import, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_202_ACCEPTED)
        count_after_second = Event.objects.count()
        self.assertEqual(count_after_first, count_after_second)

    def test_create_event_negative(self):
        data = [{
            "event_id": str(uuid.uuid4()),
            "occurred_at": timezone.now().isoformat(),
            "user_id": 1,
            "event_type": "login",
            "properties": {"country": "PL"}
        }, ]
        response = self.client.post(self.url_import, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Event.objects.count(), 0)


class DAUStatsTests(APITestCase):
    def setUp(self):
        now = timezone.now()
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=now, user_id=1, event_type="view",
                             properties={"country": "PL", "session_id": "5ef18783", "item_id": "SKU6991", "price": 118.64, "currency": "USD"})
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=now, user_id=2, event_type="view",
                             properties={"country": "PL", "session_id": "5ef18783", "item_id": "SKU6995", "price": 100.25, "currency": "USD"})
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=now, user_id=1, event_type="login",
                             properties={"country": "PL", "session_id": "533e684a", "method": "apple"})

    def test_dau(self):
        url = reverse('dau_stats')
        response = self.client.get(url, query_params={"from": timezone.now().date(), "to": timezone.now().date()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('dau' in str(response.content))


class TopEventsTests(APITestCase):
    def setUp(self):
        now = timezone.now()
        for i in range(5):
            Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=now, user_id=i, event_type="login", properties={})
        for i in range(3):
            Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=now, user_id=i + 5, event_type="purchase", properties={})

    def test_top_events(self):
        url = reverse('top_events')
        response = self.client.get(url, {"limit": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]['event_type'], 'login')


class RetentionStatsTests(APITestCase):
    def setUp(self):
        base = timezone.now() - timedelta(days=7)
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=base, user_id=11, event_type="login",
                             properties={"country": "UK", "session_id": "534e624f", "method": "google"})
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=base + timedelta(days=7), user_id=11, event_type="login",
                             properties={"country": "GE", "session_id": "554aa24d", "method": "password"})
        Event.objects.create(event_id=str(uuid.uuid4()), occurred_at=base, user_id=22, event_type="login",
                             properties={"country": "NL", "session_id": "fa17a4bc", "method": "password"})

    def test_retention_weekly(self):
        url = reverse('retention_stats')
        start = (timezone.now().date() - timedelta(days=7)).isoformat()
        response = self.client.get(url, {"start_date": start, "windows": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('retention' in response.json())


class IngestToStatsIntegrationTest(APITestCase):
    def setUp(self):
        self.url_import = reverse('ingest_events')
        self.url_dau = reverse('dau_stats')

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_ingest_and_query_stats(self):
        event_id = str(uuid.uuid4())
        event_data = [{
            "event_id": event_id,
            "occurred_at": (timezone.now() - timedelta(days=1)).isoformat(),
            "user_id": 1,
            "event_type": "view_item",
            "properties": {"item_id": "SKU123", "country": "PL", "session_id": "7ef43223"}
        }, ]
        resp_import = self.client.post(self.url_import, event_data, format='json')
        self.assertEqual(resp_import.status_code, 202)
        resp_stats = self.client.get(self.url_dau, query_params={'from': (timezone.now() - timedelta(days=2)).date(), 'to': timezone.now().date()})
        self.assertEqual(resp_stats.status_code, 200)
        stats_data = resp_stats.json()
        self.assertTrue(any(stat['dau'] > 0 for stat in stats_data))
