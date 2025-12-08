"""
Celery Configuration and Tasks
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('inventory_management')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Check low stock every day at 8 AM
    'check-low-stock-daily': {
        'task': 'apps.inventory.tasks.check_low_stock_alerts',
        'schedule': crontab(hour=8, minute=0),
    },
    # Generate daily sales report at 11 PM
    'daily-sales-report': {
        'task': 'apps.reports.tasks.generate_daily_sales_report',
        'schedule': crontab(hour=23, minute=0),
    },
    # Check pending M-Pesa transactions every 5 minutes
    'check-pending-transactions': {
        'task': 'apps.payments.tasks.check_pending_transactions',
        'schedule': crontab(minute='*/5'),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
