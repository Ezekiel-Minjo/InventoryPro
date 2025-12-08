from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product
from .models import StockMovement
from .forms import StockAdjustmentForm

# Create your views here.

def index(request):
    return HttpResponse("Inventory Home Page")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta

from apps.products.models import Product
from .models import StockMovement
from .forms import StockAdjustmentForm


@login_required
def stock_list(request):
    """Display current stock levels"""
    products = Product.objects.select_related('category').filter(is_active=True)
    
    # Calculate total value
    total_value = sum(p.stock_value for p in products)
    low_stock_count = products.filter(current_stock__lte=F('reorder_level')).count()
    out_of_stock = products.filter(current_stock=0).count()
    
    context = {
        'products': products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'inventory/stock_list.html', context)


@login_required
def low_stock(request):
    """Display products with low stock"""
    products = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('reorder_level')
    ).select_related('category').order_by('current_stock')
    
    context = {'products': products}
    return render(request, 'inventory/low_stock.html', context)


@login_required
def adjust_stock(request, product_id):
    """Adjust stock for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            movement_type = form.cleaned_data['movement_type']
            quantity = form.cleaned_data['quantity']
            reference = form.cleaned_data['reference']
            notes = form.cleaned_data['notes']
            
            stock_before = product.current_stock
            
            # Update stock
            if movement_type == 'IN':
                product.current_stock += quantity
            elif movement_type == 'OUT':
                if product.current_stock < quantity:
                    messages.error(request, 'Insufficient stock!')
                    return redirect('inventory:adjust_stock', product_id=product_id)
                product.current_stock -= quantity
            elif movement_type == 'ADJUSTMENT':
                product.current_stock = quantity
            
            product.save()
            
            # Record movement
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=quantity if movement_type != 'ADJUSTMENT' else abs(quantity - stock_before),
                reference=reference,
                notes=notes,
                stock_before=stock_before,
                stock_after=product.current_stock,
                created_by=request.user
            )
            
            messages.success(request, f'Stock adjusted for {product.name}')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = StockAdjustmentForm()
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'inventory/adjust_stock.html', context)


@login_required
def stock_movements(request):
    """Display all stock movements"""
    movements = StockMovement.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        movements = movements.filter(created_at__date__gte=start_date)
    if end_date:
        movements = movements.filter(created_at__date__lte=end_date)
    
    # Filter by movement type
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(movements, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'inventory/movements.html', context)


@login_required
def stock_report(request):
    """Generate stock report"""
    products = Product.objects.select_related('category').filter(is_active=True)
    
    # Calculate statistics
    total_products = products.count()
    total_value = sum(p.stock_value for p in products)
    low_stock = products.filter(current_stock__lte=F('reorder_level')).count()
    out_of_stock = products.filter(current_stock=0).count()
    
    # Stock by category
    from django.db.models import Count
    category_stats = products.values('category__name').annotate(
        count=Count('id'),
        total_stock=Sum('current_stock')
    ).order_by('-total_stock')
    
    context = {
        'products': products,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'category_stats': category_stats,
    }
    return render(request, 'inventory/stock_report.html', context)