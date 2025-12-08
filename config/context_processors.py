from apps.products.models import Product
from django.db.models import Sum, Count, F, Q, Avg

def inventory_context(request):
    """Add inventory alerts to all template contexts"""
    if request.user.is_authenticated:
        low_stock_count = Product.objects.filter(
            is_active=True,
            current_stock__lte=F('reorder_level')
        ).count()
        
        return {
            'low_stock_count': low_stock_count
        }
    return {}