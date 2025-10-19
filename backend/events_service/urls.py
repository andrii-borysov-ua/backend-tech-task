from django.urls import path
from .views import ingest_events, dau_stats, top_events, retention_stats

urlpatterns = [
    path('events', ingest_events, name='ingest_events'),
    path('stats/dau', dau_stats, name='dau_stats'),
    path('stats/top-events', top_events, name='top_events'),
    path('stats/retention_stats', retention_stats, name='retention_stats'),
]