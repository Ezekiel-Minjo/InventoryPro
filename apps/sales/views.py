from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
from django.db.models import Q, Sum
from .models import Sale, SaleItem
from apps.products.models import Category, Product
from apps.inventory.models import StockMovement
from apps.payments.models import Transaction
from apps.payments.daraja import DarajaAPI
from django.conf import settings
from django.http import HttpResponse

# Create your views here.


@login_required
def sales_list(request):
    """Display list of all sales"""
    sales = Sale.objects.all().select_related('created_by')
    
    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        sales = sales.filter(created_at__date__gte=start_date)
    if end_date:
        sales = sales.filter(created_at__date__lte=end_date)
    
    context = {
        'sales': sales,
        'total_sales': sum(sale.total_amount for sale in sales),
    }
    return render(request, 'sales/sales_list.html', context)


@login_required
def new_sale(request):
    """Create new sale - POS interface"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create sale
                sale = Sale.objects.create(
                    customer_name=data.get('customer_name', ''),
                    customer_phone=data.get('customer_phone', ''),
                    payment_method=data.get('payment_method', 'CASH'),
                    created_by=request.user
                )
                
                total_amount = Decimal('0.00')
                items = data.get('items', [])
                
                # Process each item
                for item_data in items:
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    
                    # Check stock availability
                    if product.current_stock < quantity:
                        return JsonResponse({
                            'success': False,
                            'error': f'Insufficient stock for {product.name}'
                        }, status=400)
                    
                    # Create sale item
                    sale_item = SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=product.selling_price
                    )
                    
                    total_amount += sale_item.subtotal
                    
                    # Update stock
                    product.current_stock -= quantity
                    product.save()
                    
                    # Record stock movement
                    StockMovement.objects.create(
                        product=product,
                        movement_type='OUT',
                        quantity=quantity,
                        reference=sale.sale_number,
                        notes=f'Sale {sale.sale_number}',
                        stock_before=product.current_stock + quantity,
                        stock_after=product.current_stock,
                        created_by=request.user
                    )
                
                # Update sale total
                sale.total_amount = total_amount
                sale.save()
                
                # Handle M-Pesa payment
                if sale.payment_method == 'MPESA':
                    return initiate_mpesa_payment(sale)
                
                return JsonResponse({
                    'success': True,
                    'sale_id': sale.id,
                    'sale_number': sale.sale_number,
                    'total_amount': str(sale.total_amount)
                })
                
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - render POS interface
    products = Product.objects.filter(is_active=True, current_stock__gt=0)
    categories = Category.objects.filter(products__in=products).distinct()
    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'sales/new_sale.html', context)


def initiate_mpesa_payment(sale):
    """Initiate M-Pesa STK Push for sale payment"""
    try:
        daraja = DarajaAPI()
        
        # Initiate STK Push
        result = daraja.stk_push(
            phone_number=sale.customer_phone,
            amount=sale.total_amount,
            account_reference=sale.sale_number,
            transaction_desc=f'Payment for {sale.sale_number}',
            callback_url=settings.MPESA_CALLBACK_URL
        )
        
        if result['success']:
            # Create transaction record
            mpesa_transaction = Transaction.objects.create(
                transaction_type='STK_PUSH',
                amount=sale.total_amount,
                phone_number=sale.customer_phone,
                merchant_request_id=result['merchant_request_id'],
                checkout_request_id=result['checkout_request_id'],
                status='PENDING',
                sale=sale
            )
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'message': 'Payment request sent to customer phone',
                'checkout_request_id': result['checkout_request_id']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Payment initiation failed')
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'M-Pesa error: {str(e)}'
        }, status=500)


@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa callback for STK Push"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract callback data
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            # Find transaction
            mpesa_transaction = Transaction.objects.get(
                checkout_request_id=checkout_request_id
            )
            
            if result_code == 0:  # Success
                # Extract metadata
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                mpesa_receipt = None
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt = item.get('Value')
                        break
                
                # Update transaction
                mpesa_transaction.status = 'SUCCESS'
                mpesa_transaction.mpesa_receipt_number = mpesa_receipt
                mpesa_transaction.result_desc = result_desc
                mpesa_transaction.save()
                
                # Update sale
                if mpesa_transaction.sale:
                    mpesa_transaction.sale.mpesa_transaction_id = mpesa_receipt
                    mpesa_transaction.sale.save()
                
            else:  # Failed
                mpesa_transaction.status = 'FAILED'
                mpesa_transaction.result_desc = result_desc
                mpesa_transaction.save()
            
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            
        except Transaction.DoesNotExist:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Transaction not found'})
        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'})


@login_required
def sale_detail(request, sale_id):
    """View sale details and print receipt"""
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.select_related('product')
    
    context = {
        'sale': sale,
        'items': items,
    }
    return render(request, 'sales/sale_detail.html', context)


@login_required
def check_payment_status(request, checkout_request_id):
    """Check M-Pesa payment status"""
    try:
        mpesa_transaction = Transaction.objects.get(
            checkout_request_id=checkout_request_id
        )
        
        if mpesa_transaction.status == 'PENDING':
            # Query M-Pesa for status
            daraja = DarajaAPI()
            result = daraja.stk_push_query(checkout_request_id)
            
            if result['success'] and result['result_code'] == '0':
                mpesa_transaction.status = 'SUCCESS'
                mpesa_transaction.save()
        
        return JsonResponse({
            'status': mpesa_transaction.status,
            'result_desc': mpesa_transaction.result_desc,
            'mpesa_receipt': mpesa_transaction.mpesa_receipt_number
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({
            'error': 'Transaction not found'
        }, status=404)


@login_required
def search_product(request):
    """Search product by name, SKU, or barcode"""
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            is_active=True
        ).filter(
            models.Q(name__icontains=query) |
            models.Q(sku__icontains=query) |
            models.Q(barcode__icontains=query)
        )[:10]
        
        results = [{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode,
            'selling_price': str(p.selling_price),
            'current_stock': p.current_stock,
            'image': p.image.url if p.image else None
        } for p in products]
        
        return JsonResponse({'products': results})
    
    return JsonResponse({'products': []})


@login_required
def daily_sales_report(request):
    """Generate daily sales report"""
    today = timezone.now().date()
    sales = Sale.objects.filter(created_at__date=today)
    
    total_sales = sum(sale.total_amount for sale in sales)
    total_transactions = sales.count()
    cash_sales = sales.filter(payment_method='CASH').aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    mpesa_sales = sales.filter(payment_method='MPESA').aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    
    context = {
        'date': today,
        'sales': sales,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'cash_sales': cash_sales,
        'mpesa_sales': mpesa_sales,
    }
    
    return render(request, 'sales/daily_report.html', context)


@login_required
def refund_sale(request, sale_id):
    """Process refund via M-Pesa B2C"""
    sale = get_object_or_404(Sale, id=sale_id)
    
    if request.method == 'POST':
        try:
            refund_amount = Decimal(request.POST.get('refund_amount', sale.total_amount))
            
            if refund_amount > sale.total_amount:
                messages.error(request, 'Refund amount cannot exceed sale amount')
                return redirect('sale_detail', sale_id=sale_id)
            
            # Initiate B2C payment for refund
            daraja = DarajaAPI()
            result = daraja.b2c_payment(
                phone_number=sale.customer_phone,
                amount=refund_amount,
                occasion='Refund',
                remarks=f'Refund for sale {sale.sale_number}',
                result_url=settings.MPESA_RESULT_URL,
                timeout_url=settings.MPESA_TIMEOUT_URL
            )
            
            if result['success']:
                # Create transaction record
                Transaction.objects.create(
                    transaction_type='REFUND',
                    amount=refund_amount,
                    phone_number=sale.customer_phone,
                    conversation_id=result['conversation_id'],
                    originator_conversation_id=result['originator_conversation_id'],
                    status='PENDING',
                    sale=sale
                )
                
                messages.success(request, 'Refund initiated successfully')
            else:
                messages.error(request, f"Refund failed: {result.get('error')}")
            
            return redirect('sale_detail', sale_id=sale_id)
            
        except Exception as e:
            messages.error(request, f'Error processing refund: {str(e)}')
            return redirect('sale_detail', sale_id=sale_id)
    
    context = {'sale': sale}
    return render(request, 'sales/refund_form.html', context)

def index(request):
    return HttpResponse("Sales Home Page")