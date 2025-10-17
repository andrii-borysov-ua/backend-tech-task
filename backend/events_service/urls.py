from django.urls import path
from .views import ingest_events

urlpatterns = [
    path('events', ingest_events, name='ingest_events'),
]