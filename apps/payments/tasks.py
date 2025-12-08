# apps/payments/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import Transaction
from .daraja import DarajaAPI


@shared_task
def check_pending_transactions():
    """
    Check status of pending M-Pesa transactions
    Runs every 5 minutes
    """
    # Get pending transactions older than 2 minutes
    cutoff_time = timezone.now() - timedelta(minutes=2)
    pending_transactions = Transaction.objects.filter(
        status='PENDING',
        created_at__lt=cutoff_time
    )
    
    if not pending_transactions.exists():
        return "No pending transactions"
    
    daraja = DarajaAPI()
    updated_count = 0
    
    for transaction in pending_transactions:
        if transaction.checkout_request_id:
            # Query STK Push status
            result = daraja.stk_push_query(transaction.checkout_request_id)
            
            if result['success']:
                if result['result_code'] == '0':
                    transaction.status = 'SUCCESS'
                    transaction.result_desc = result.get('result_desc', 'Success')
                elif result['result_code'] != '':
                    transaction.status = 'FAILED'
                    transaction.result_desc = result.get('result_desc', 'Failed')
                
                transaction.save()
                updated_count += 1
    
    return f"Updated {updated_count} transactions"


@shared_task
def timeout_old_pending_transactions():
    """
    Mark very old pending transactions as cancelled
    Runs daily
    """
    # Transactions pending for more than 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    old_transactions = Transaction.objects.filter(
        status='PENDING',
        created_at__lt=cutoff_time
    )
    
    count = old_transactions.update(
        status='CANCELLED',
        result_desc='Timeout - No response after 24 hours'
    )
    
    return f"Cancelled {count} old pending transactions"