# api/views.py
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_connected = True
    except:
        db_connected = False

    return JsonResponse({
        'status': 'healthy',
        'database_connected': db_connected,
        'database_engine': connection.vendor,
        'database_name': connection.settings_dict['NAME'],
    })