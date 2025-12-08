# apps/inventory/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import F

from apps.products.models import Product


@shared_task
def check_low_stock_alerts():
    """
    Check for low stock products and send email alerts
    Runs daily at 8 AM
    """
    if not settings.LOW_STOCK_ALERT_ENABLED:
        return "Low stock alerts disabled"
    
    # Get products with low stock
    low_stock_products = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('reorder_level')
    ).select_related('category')
    
    if not low_stock_products.exists():
        return "No low stock products"
    
    # Group by severity
    out_of_stock = [p for p in low_stock_products if p.current_stock == 0]
    critically_low = [p for p in low_stock_products if 0 < p.current_stock <= p.reorder_level // 2]
    low = [p for p in low_stock_products if p.current_stock > p.reorder_level // 2]
    
    # Prepare email context
    context = {
        'date': timezone.now(),
        'out_of_stock': out_of_stock,
        'critically_low': critically_low,
        'low': low,
        'total_count': low_stock_products.count(),
    }
    
    # Render email
    subject = f'Low Stock Alert - {low_stock_products.count()} Items Need Attention'
    html_message = render_to_string('emails/low_stock_alert.html', context)
    plain_message = f"""
    Low Stock Alert - {timezone.now().strftime('%Y-%m-%d')}
    
    Out of Stock: {len(out_of_stock)} items
    Critically Low: {len(critically_low)} items
    Low Stock: {len(low)} items
    
    Total: {low_stock_products.count()} items need attention
    
    Please log in to the system to view details and take action.
    """
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.LOW_STOCK_ALERT_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        return f"Alert sent for {low_stock_products.count()} products"
    except Exception as e:
        return f"Error sending alert: {str(e)}"


@shared_task
def notify_restock_needed(product_id):
    """
    Send immediate notification when a product reaches reorder level
    """
    try:
        product = Product.objects.get(id=product_id)
        
        if not product.is_low_stock:
            return "Product stock is sufficient"
        
        subject = f'Restock Alert: {product.name}'
        message = f"""
        Product: {product.name}
        SKU: {product.sku}
        Current Stock: {product.current_stock}
        Reorder Level: {product.reorder_level}
        
        Immediate action required!
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.LOW_STOCK_ALERT_EMAIL],
            fail_silently=False,
        )
        
        return f"Restock notification sent for {product.name}"
    except Product.DoesNotExist:
        return "Product not found"
    except Exception as e:
        return f"Error: {str(e)}"