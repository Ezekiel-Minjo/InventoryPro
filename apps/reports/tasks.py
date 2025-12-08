from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from apps.sales.models import Sale, SaleItem



@shared_task
def generate_daily_sales_report():
    """
    Generate and email daily sales report
    Runs at 11 PM every day
    """
    today = timezone.now().date()
    sales = Sale.objects.filter(created_at__date=today)
    
    if not sales.exists():
        return "No sales today"
    
    # Calculate statistics
    total_sales = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    
    cash_sales = sales.filter(payment_method='CASH').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    mpesa_sales = sales.filter(payment_method='MPESA').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Top selling products
    top_products = SaleItem.objects.filter(
        sale__created_at__date=today
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_revenue')[:5]
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Daily Sales Report - {today}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Summary
    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', f'KES {total_sales:,.2f}'],
        ['Transactions', str(total_transactions)],
        ['Cash Sales', f'KES {cash_sales:,.2f}'],
        ['M-Pesa Sales', f'KES {mpesa_sales:,.2f}'],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Top products
    if top_products:
        elements.append(Paragraph("Top Selling Products", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        product_data = [['Product', 'Quantity', 'Revenue']]
        for item in top_products:
            product_data.append([
                item['product__name'],
                str(item['total_quantity']),
                f"KES {item['total_revenue']:,.2f}"
            ])
        
        product_table = Table(product_data)
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(product_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    # Send email
    email = EmailMessage(
        subject=f'Daily Sales Report - {today}',
        body=f'Please find attached the daily sales report for {today}.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.LOW_STOCK_ALERT_EMAIL]
    )
    email.attach(f'sales_report_{today}.pdf', buffer.getvalue(), 'application/pdf')
    
    try:
        email.send()
        return f"Daily report sent for {today}"
    except Exception as e:
        return f"Error sending report: {str(e)}"


@shared_task
def generate_weekly_inventory_report():
    """
    Generate weekly inventory status report
    """
    from apps.products.models import Product
    from django.db.models import F
    
    # Get inventory statistics
    products = Product.objects.filter(is_active=True)
    total_products = products.count()
    total_value = sum(p.stock_value for p in products)
    low_stock = products.filter(current_stock__lte=F('reorder_level')).count()
    out_of_stock = products.filter(current_stock=0).count()
    
    subject = 'Weekly Inventory Report'
    message = f"""
    Weekly Inventory Report
    
    Total Products: {total_products}
    Total Inventory Value: KES {total_value:,.2f}
    Low Stock Items: {low_stock}
    Out of Stock Items: {out_of_stock}
    
    Please review the inventory and take necessary action.
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.LOW_STOCK_ALERT_EMAIL],
            fail_silently=False,
        )
        return "Weekly inventory report sent"
    except Exception as e:
        return f"Error: {str(e)}"