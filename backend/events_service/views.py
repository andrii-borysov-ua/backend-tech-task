from .models import Event
from .serializers import EventSerializer
from datetime import timedelta
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging


logger = logging.getLogger(__name__)


@swagger_auto_schema(method='post',
                     request_body=EventSerializer(many=True),
                     responses={201: "Events ingested successfully", 400: "Validation errors"},
                     operation_id='Ingest events')
@api_view(['POST'])
def ingest_events(request):
    logger.info('Ingest events')
    if not isinstance(request.data, list):
        logger.debug(request.data)
        logger.error('Ingest events request body is not a list')
        return Response({"error": "Expected a list of events"}, status=status.HTTP_400_BAD_REQUEST)
    created_count = 0
    skipped_count = 0
    with transaction.atomic():
        for event_data in request.data:
            serializer = EventSerializer(data=event_data)
            if serializer.is_valid():
                event, created = Event.objects.get_or_create(event_id=serializer.validated_data['event_id'], defaults=serializer.validated_data)
                if created:
                    created_count += 1
                else:
                    skipped_count += 1
            else:
                logger.error(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    logger.info(f'processed: {len(request.data)}, created: {created_count}, skipped: {skipped_count}')
    return Response({"processed": len(request.data), "created": created_count, "skipped": skipped_count}, status=status.HTTP_201_CREATED)


from_param = openapi.Parameter('from', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)",
                               type=openapi.TYPE_STRING, format='date')
to_param = openapi.Parameter('to', openapi.IN_QUERY, description="End date (YYYY-MM-DD)",
                             type=openapi.TYPE_STRING, format='date')

@swagger_auto_schema(method='get',
                     manual_parameters=[from_param, to_param],
                     operation_id="Get DAU (Daily Active Users)")
@api_view(['GET'])
def dau_stats(request):
    logger.info('GET DAU stats')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    query = Event.objects.all()

    if date_from: query = query.filter(occurred_at__date__gte=date_from)
    if date_to: query = query.filter(occurred_at__date__lte=date_to)

    stats = (
        query.annotate(day=TruncDate('occurred_at')).values('day').annotate(dau=Count('user_id', distinct=True)).order_by('day')
    )
    return Response(list(stats), status=status.HTTP_200_OK)


optional_from_param = openapi.Parameter('from', openapi.IN_QUERY, description="Start date (YYYY-MM-DD)",
                                        type=openapi.TYPE_STRING, format='date', required=False)
optional_to_param = openapi.Parameter('to', openapi.IN_QUERY, description="End date (YYYY-MM-DD)",
                                      type=openapi.TYPE_STRING, format='date', required=False)
optional_limit_param = openapi.Parameter('limit', openapi.IN_QUERY, description="Number of Top events (10 by default)",
                                         type=openapi.TYPE_INTEGER, required=False)


@swagger_auto_schema(method='get',
                     manual_parameters=[optional_from_param, optional_to_param, optional_limit_param],
                     operation_id="Top events for the selected period of time")
@api_view(['GET'])
def top_events(request):
    logger.info('GET Top events')
    date_to = request.GET.get('to', timezone.now().date())
    date_from = request.GET.get('from', date_to - timedelta(days=30))
    limit = request.GET.get('limit', 10)

    try:
        limit = int(limit)
        if limit <= 0: raise ValueError
    except (ValueError, TypeError):
        logger.error(f'Invalid limit value: {limit}')
        return Response({"error": "limit must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

    query = Event.objects.filter(occurred_at__date__gte=date_from, occurred_at__date__lte=date_to)
    stats = (query.values('event_type').annotate(count=Count('event_type')).order_by('-count')[:limit])
    return Response(list(stats), status=status.HTTP_200_OK)


start_date_param = openapi.Parameter('start_date', openapi.IN_QUERY, description="Start date for cohort in YYYY-MM-DD format (required)",
                                     type=openapi.TYPE_STRING, format='date', required=True)
windows_param = openapi.Parameter('windows', openapi.IN_QUERY, description="Number of weekly windows to analyze retention",
                                  type=openapi.TYPE_INTEGER, required=False, default=3)

@swagger_auto_schema(method='get',
                     manual_parameters=[start_date_param, windows_param],
                     operation_id="Simple weekly cohort retention analysis")
@api_view(['GET'])
def retention_stats(request):
    logger.info('GET Retention stats')
    start_date_str = request.GET.get('start_date')
    windows = request.GET.get('windows', 3)

    if not start_date_str:
        logger.error(f'Missing start date')
        return Response({"error": "start_date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start_date = parse_date(start_date_str)
        if start_date is None: raise ValueError
    except ValueError:
        logger.error(f'Invalid start date {start_date_str}')
        return Response({"error": "start_date must be in YYYY-MM-DD format"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        windows = int(windows)
        if windows < 1: raise ValueError
    except ValueError:
        logger.error(f'Invalid windows {windows}')
        return Response({"error": "windows must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

    cohort_users = Event.objects.filter(occurred_at__date=start_date).values_list('user_id', flat=True).distinct()

    retention = {}
    for week in range(windows):
        check_start = start_date + timedelta(weeks=week)
        check_end = check_start + timedelta(days=6)  # тиждень = 7 днів
        active_users = Event.objects.filter(occurred_at__date__gte=check_start, occurred_at__date__lte=check_end, user_id__in=cohort_users).values('user_id').distinct().count()
        retention[str(check_start) + " to " + str(check_end)] = active_users

    return Response({"start_date": str(start_date), "windows": windows, "retention": retention}, status=status.HTTP_200_OK)
