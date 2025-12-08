
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
import json

from apps.products.models import Product
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import StockMovement


@login_required
def dashboard(request):
    """
    Main dashboard view - First page after login
    Shows overview statistics, charts, and alerts
    """
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ============================================
    # STATISTICS FOR TOP CARDS
    # ============================================
    
    # Total active products
    total_products = Product.objects.filter(is_active=True).count()
    active_products = Product.objects.filter(is_active=True).count()
    
    # Low stock count
    low_stock_count = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('reorder_level')
    ).count()
    
    # Today's sales
    today_sales = Sale.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    today_transactions = Sale.objects.filter(
        created_at__date=today
    ).count()
    
    # Total inventory value (at cost price)
    all_products = Product.objects.filter(is_active=True)
    inventory_value = sum(
        product.current_stock * product.cost_price 
        for product in all_products
    )
    
    stats = {
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_count': low_stock_count,
        'today_sales': float(today_sales),
        'today_transactions': today_transactions,
        'inventory_value': float(inventory_value),
    }
    
    # ============================================
    # LOW STOCK PRODUCTS (Top 10)
    # ============================================
    low_stock_products = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('reorder_level')
    ).select_related('category').order_by('current_stock')[:10]
    
    # ============================================
    # RECENT SALES (Last 10)
    # ============================================
    recent_sales = Sale.objects.select_related(
        'created_by'
    ).prefetch_related('items').order_by('-created_at')[:10]
    
    # ============================================
    # TOP SELLING PRODUCTS (This Month)
    # ============================================
    top_products = SaleItem.objects.filter(
        sale__created_at__gte=month_ago
    ).values(
        'product__name', 
        'product__sku', 
        'product__category__name',
        'product__current_stock',
        'product__reorder_level'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:10]
    
    # Add is_low_stock flag to top products
    for product in top_products:
        product['product__is_low_stock'] = (
            product['product__current_stock'] <= product['product__reorder_level']
        )
    
    # ============================================
    # SALES TREND - Last 7 Days (For Chart)
    # ============================================
    sales_by_day = []
    labels = []
    
    for i in range(6, -1, -1):  # Last 7 days
        date = today - timedelta(days=i)
        
        daily_sales = Sale.objects.filter(
            created_at__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        sales_by_day.append(float(daily_sales))
        labels.append(date.strftime('%a %d'))  # e.g., "Mon 04"
    
    # ============================================
    # PAYMENT METHOD DISTRIBUTION (This Month)
    # ============================================
    payment_stats = Sale.objects.filter(
        created_at__gte=month_ago
    ).values('payment_method').annotate(
        total=Sum('total_amount')
    )
    
    # Initialize payment data
    payment_data = {
        'MPESA': 0,
        'CASH': 0,
        'CARD': 0
    }
    
    # Fill in actual data
    for item in payment_stats:
        if item['payment_method'] in payment_data:
            payment_data[item['payment_method']] = float(item['total'])
    
    # ============================================
    # CATEGORY SALES (This Month)
    # ============================================
    category_sales = SaleItem.objects.filter(
        sale__created_at__gte=month_ago
    ).values(
        'product__category__name'
    ).annotate(
        total_revenue=Sum('subtotal'),
        total_items=Sum('quantity')
    ).order_by('-total_revenue')[:5]
    
    # ============================================
    # PREPARE CONTEXT FOR TEMPLATE
    # ============================================
    context = {
        # Statistics for cards
        'stats': stats,
        
        # Low stock products table
        'low_stock_products': low_stock_products,
        
        # Recent sales table
        'recent_sales': recent_sales,
        
        # Top selling products
        'top_products': top_products,
        
        # Sales trend chart data (JSON for Chart.js)
        'sales_labels': json.dumps(labels),
        'sales_data': json.dumps(sales_by_day),
        
        # Payment method chart data (JSON for Chart.js)
        'payment_data': json.dumps([
            payment_data['MPESA'],
            payment_data['CASH'],
            payment_data['CARD']
        ]),
        
        # Category sales
        'category_sales': category_sales,
    }
    
    return render(request, 'dashboard.html', context)


# Alternative: Redirect root URL to dashboard
def home(request):
    """Root URL - Redirect to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')
