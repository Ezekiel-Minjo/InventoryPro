from django.contrib import admin
from .models import Category, Product
from django.utils.html import format_html

# Register your models here.

# admin.site.register(Category)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    product_count.short_description = 'Products'

# admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'display_image', 'cost_price',
        'selling_price', 'stock_status', 'profit_margin_display',
        'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'barcode']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'barcode', 'category', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price')
        }),
        ('Inventory', {
            'fields': ('current_stock', 'reorder_level')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    display_image.short_description = 'Image'
    
    def stock_status(self, obj):
        if obj.current_stock == 0:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">OUT</span>'
            )
        elif obj.is_low_stock:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} (LOW)</span>',
                obj.current_stock
            )
        else:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
                obj.current_stock
            )
    stock_status.short_description = 'Stock'
    
    def profit_margin_display(self, obj):
        margin = obj.profit_margin
        color = '#198754' if margin > 30 else '#ffc107' if margin > 15 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, round(margin, 1)
        )
    profit_margin_display.short_description = 'Margin'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new product
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_active', 'mark_as_inactive', 'apply_discount']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products marked as active.')
    mark_as_active.short_description = 'Mark selected as active'
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected as inactive'    
