from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from .forms import SupplierForm, PurchaseOrderForm
from apps.payments.daraja import DarajaAPI
from apps.payments.models import Transaction
from apps.products.models import Product
from apps.inventory.models import StockMovement
from django.conf import settings
from decimal import Decimal



@login_required
def supplier_list(request):
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_detail(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    purchase_orders = supplier.purchase_orders.all()
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'purchase_orders': purchase_orders
    })


@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier created successfully!')
            return redirect('suppliers:supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'suppliers/supplier_form.html', {'form': form})


@login_required
def supplier_update(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully!')
            return redirect('suppliers:supplier_detail', supplier_id=supplier_id)
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'suppliers/supplier_form.html', {
        'form': form,
        'supplier': supplier
    })


@login_required
def purchase_order_list(request):
    pos = PurchaseOrder.objects.select_related('supplier').all()
    return render(request, 'suppliers/purchase_order_list.html', {'purchase_orders': pos})


@login_required
def purchase_order_detail(request, po_id):
    po = get_object_or_404(PurchaseOrder, id=po_id)
    items = po.items.select_related('product')
    return render(request, 'suppliers/purchase_order_detail.html', {
        'po': po,
        'items': items
    })


@login_required
def purchase_order_create(request):
    # Implementation for creating PO with items
    # This would be a more complex form with inline formsets
    pass


@login_required
def pay_supplier(request, po_id):
    """Pay supplier via M-Pesa B2C"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        
        try:
            daraja = DarajaAPI()
            result = daraja.b2c_payment(
                phone_number=po.supplier.phone_number,
                amount=amount,
                occasion='Supplier Payment',
                remarks=f'Payment for {po.po_number}',
                result_url=settings.MPESA_RESULT_URL,
                timeout_url=settings.MPESA_TIMEOUT_URL
            )
            
            if result['success']:
                # Create transaction record
                Transaction.objects.create(
                    transaction_type='B2C',
                    amount=amount,
                    phone_number=po.supplier.phone_number,
                    conversation_id=result['conversation_id'],
                    originator_conversation_id=result['originator_conversation_id'],
                    status='PENDING',
                    purchase_order=po
                )
                
                # Update PO paid amount
                po.paid_amount += Decimal(amount)
                po.save()
                
                messages.success(request, 'Payment initiated successfully!')
            else:
                messages.error(request, f"Payment failed: {result.get('error')}")
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('suppliers:purchase_order_detail', po_id=po_id)
    
    return render(request, 'suppliers/pay_supplier.html', {'po': po})


@login_required
def receive_purchase_order(request, po_id):
    """Mark PO as received and update stock"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Update stock for each item
            for item in po.items.all():
                product = item.product
                stock_before = product.current_stock
                product.current_stock += item.quantity
                product.save()
                
                # Record stock movement
                StockMovement.objects.create(
                    product=product,
                    movement_type='IN',
                    quantity=item.quantity,
                    reference=po.po_number,
                    notes=f'Received from {po.supplier.name}',
                    stock_before=stock_before,
                    stock_after=product.current_stock,
                    created_by=request.user
                )
            
            # Update PO status
            po.status = 'RECEIVED'
            po.received_date = timezone.now().date()
            po.save()
            
            messages.success(request, f'Purchase Order {po.po_number} received and stock updated!')
        
        return redirect('suppliers:purchase_order_detail', po_id=po_id)
    
    return render(request, 'suppliers/receive_po.html', {'po': po})