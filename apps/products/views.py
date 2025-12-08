from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Product, Category
from .forms import ProductForm, CategoryForm
from apps.inventory.models import StockMovement

# Create your views here.

def index(request):
    return HttpResponse("Products Home Page")




@login_required
def product_list(request):
    """Display list of all products"""
    products = Product.objects.select_related('category').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Stock filter
    stock_filter = request.GET.get('stock')
    if stock_filter == 'low':
        products = products.filter(current_stock__lte=F('reorder_level'))
    elif stock_filter == 'out':
        products = products.filter(current_stock=0)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, product_id):
    """View product details"""
    product = get_object_or_404(Product, id=product_id)
    stock_movements = StockMovement.objects.filter(product=product).order_by('-created_at')[:20]
    
    # Calculate statistics
    total_sold = StockMovement.objects.filter(
        product=product,
        movement_type='OUT'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    total_received = StockMovement.objects.filter(
        product=product,
        movement_type='IN'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'product': product,
        'stock_movements': stock_movements,
        'total_sold': total_sold,
        'total_received': total_received,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            
            # Create initial stock movement if stock > 0
            if product.current_stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type='IN',
                    quantity=product.current_stock,
                    reference='Initial Stock',
                    notes='Initial stock entry',
                    stock_before=0,
                    stock_after=product.current_stock,
                    created_by=request.user
                )
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {'form': form, 'action': 'Create'})


@login_required
def product_update(request, product_id):
    """Update product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('products:product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'action': 'Update'
    })


@login_required
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('products:product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {'form': form})