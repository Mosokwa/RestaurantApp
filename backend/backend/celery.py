from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'update-popularity-scores-daily': {
        'task': 'api.tasks.update_popularity_scores_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-user-preferences-weekly': {
        'task': 'api.tasks.update_user_preferences_task', 
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday at 3 AM
    },
    'cleanup-old-recommendations': {
        'task': 'api.tasks.cleanup_old_recommendations_task',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    'calculate-item-associations': {
        'task': 'api.tasks.calculate_item_associations_task',
        'schedule': crontab(day_of_week=1, hour=1, minute=0),
    },

    # ========== NEW SCHEDULES - REAL-TIME SYNC & MONITORING ==========
    'periodic-pos-menu-sync': {
        'task': 'api.tasks.periodic_pos_menu_sync',
        'schedule': crontab(minute='*/15', hour='6-22'),  # Every 15 minutes during business hours
    },
    'periodic-pos-inventory-sync': {
        'task': 'api.tasks.periodic_pos_inventory_sync',
        'schedule': crontab(minute='*/30', hour='6-22'),  # Every 30 minutes during business hours
    },
    'system-health-check': {
        'task': 'api.tasks.run_system_health_check',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'resolve-data-conflicts': {
        'task': 'api.tasks.resolve_data_conflicts',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'cleanup-websocket-connections': {
        'task': 'api.tasks.cleanup_old_websocket_connections',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')