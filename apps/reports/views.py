from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import csv

from apps.products.models import Product, Category
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import StockMovement
from apps.suppliers.models import Supplier


@login_required
def reports_dashboard(request):
    """Reports overview page"""
    
    # Get some basic stats
    from apps.sales.models import Sale
    from apps.products.models import Product
    from apps.suppliers.models import Supplier
    
    total_products = Product.objects.filter(is_active=True).count()
    total_sales = Sale.objects.count()
    total_customers = Sale.objects.exclude(customer_name='').values('customer_phone').distinct().count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    
    context = {
        'available_reports': [
            {
                'name': 'Sales Report',
                'description': 'Detailed sales analysis with trends',
                'url': 'reports:sales_report',
                'icon': 'graph-up'
            },
            {
                'name': 'Inventory Report',
                'description': 'Current stock levels and valuation',
                'url': 'reports:inventory_report',
                'icon': 'boxes'
            },
            {
                'name': 'Profit Analysis',
                'description': 'Profit margins and revenue breakdown',
                'url': 'reports:profit_report',
                'icon': 'currency-dollar'
            },
            {
                'name': 'Stock Movement Report',
                'description': 'Track all stock movements',
                'url': 'reports:movement_report',
                'icon': 'arrow-left-right'
            },
        ],
        'total_products': total_products,
        'total_sales': total_sales,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def sales_report(request):
    """Detailed sales report with filtering"""
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get sales
    sales = Sale.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Calculate statistics
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    average_sale = total_sales / total_transactions if total_transactions > 0 else 0
    
    # Payment method breakdown
    payment_breakdown = sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )
    
    # Daily sales
    daily_sales = sales.extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('date')
    
    # Top customers
    top_customers = sales.exclude(
        customer_name=''
    ).values('customer_name', 'customer_phone').annotate(
        total_spent=Sum('total_amount'),
        visit_count=Count('id')
    ).order_by('-total_spent')[:10]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'average_sale': average_sale,
        'payment_breakdown': payment_breakdown,
        'daily_sales': daily_sales,
        'top_customers': top_customers,
    }
    
    return render(request, 'reports/sales_report.html', context)


@login_required
def inventory_report(request):
    """Current inventory status report"""
    products = Product.objects.filter(is_active=True).select_related('category')
    
    # Calculate totals
    total_products = products.count()
    total_value = sum(p.stock_value for p in products)
    total_selling_value = sum(p.current_stock * p.selling_price for p in products)
    potential_profit = total_selling_value - total_value
    
    # Stock status
    in_stock = products.filter(current_stock__gt=F('reorder_level')).count()
    low_stock = products.filter(
        current_stock__gt=0,
        current_stock__lte=F('reorder_level')
    ).count()
    out_of_stock = products.filter(current_stock=0).count()
    
    # Category breakdown
    category_breakdown = products.values(
        'category__name'
    ).annotate(
        product_count=Count('id'),
        total_stock=Sum('current_stock'),
        total_value=Sum(F('current_stock') * F('cost_price'))
    ).order_by('-total_value')
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_value': total_value,
        'total_selling_value': total_selling_value,
        'potential_profit': potential_profit,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'category_breakdown': category_breakdown,
    }
    
    return render(request, 'reports/inventory_report.html', context)


@login_required
def profit_report(request):
    """Profit analysis report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get sales items for profit calculation
    sale_items = SaleItem.objects.filter(
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=end_date
    ).select_related('product', 'sale')
    
    # Calculate profit per item
    profit_data = []
    total_revenue = 0
    total_cost = 0
    
    for item in sale_items:
        revenue = float(item.subtotal)
        cost = float(item.product.cost_price * item.quantity)
        profit = revenue - cost
        
        total_revenue += revenue
        total_cost += cost
        
        profit_data.append({
            'product': item.product.name,
            'quantity': item.quantity,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': (profit / revenue * 100) if revenue > 0 else 0
        })
    
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Top profitable products
    from collections import defaultdict
    product_profits = defaultdict(lambda: {'revenue': 0, 'cost': 0, 'profit': 0, 'quantity': 0})
    
    for item in sale_items:
        key = item.product.name
        product_profits[key]['revenue'] += float(item.subtotal)
        product_profits[key]['cost'] += float(item.product.cost_price * item.quantity)
        product_profits[key]['profit'] = product_profits[key]['revenue'] - product_profits[key]['cost']
        product_profits[key]['quantity'] += item.quantity
    
    top_products = sorted(product_profits.items(), key=lambda x: x[1]['profit'], reverse=True)[:10]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'profit_data': profit_data[:50],  # Limit to 50 items for display
        'top_products': top_products,
    }
    
    return render(request, 'reports/profit_report.html', context)


@login_required
def movement_report(request):
    """Stock movement report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=7)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get movements
    movements = StockMovement.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('product', 'created_by').order_by('-created_at')
    
    # Statistics
    total_in = movements.filter(movement_type='IN').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    total_out = movements.filter(movement_type='OUT').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    adjustments = movements.filter(movement_type='ADJUSTMENT').count()
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'movements': movements[:100],  # Limit to 100 for display
        'total_in': total_in,
        'total_out': total_out,
        'adjustments': adjustments,
        'total_movements': movements.count(),
    }
    
    return render(request, 'reports/movement_report.html', context)


@login_required
def export_sales_csv(request):
    """Export sales to CSV"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    sales = Sale.objects.all()
    
    if start_date:
        sales = sales.filter(created_at__date__gte=start_date)
    if end_date:
        sales = sales.filter(created_at__date__lte=end_date)
    
    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Sale Number', 'Date', 'Customer', 'Phone',
        'Payment Method', 'Total Amount', 'Items', 'Staff'
    ])
    
    for sale in sales:
        writer.writerow([
            sale.sale_number,
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
            sale.customer_name or 'Walk-in',
            sale.customer_phone or '-',
            sale.get_payment_method_display(),
            sale.total_amount,
            sale.items.count(),
            sale.created_by.username if sale.created_by else '-'
        ])
    
    return response


@login_required
def export_inventory_pdf(request):
    """Export inventory report to PDF"""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="inventory_report_{timezone.now().date()}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Inventory Report - {timezone.now().strftime('%B %d, %Y')}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Get products
    products = Product.objects.filter(is_active=True).select_related('category')
    
    # Summary
    total_value = sum(p.stock_value for p in products)
    summary = Paragraph(f"<b>Total Inventory Value:</b> KES {total_value:,.2f}", styles['Normal'])
    elements.append(summary)
    elements.append(Spacer(1, 20))
    
    # Products table
    data = [['Product', 'SKU', 'Category', 'Stock', 'Value']]
    
    for product in products[:50]:  # Limit to 50 products
        data.append([
            product.name[:30],
            product.sku,
            product.category.name if product.category else '-',
            str(product.current_stock),
            f"KES {product.stock_value:,.2f}"
        ])
    
    table = Table(data, colWidths=[3*inch, 1*inch, 1.5*inch, 0.8*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response