from django.contrib import admin
from .models import Sale, SaleItem
from django.utils.html import format_html

# Register your models here.
# admin.site.register(Sale)
# admin.site.register(SaleItem)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['product', 'quantity', 'unit_price', 'subtotal']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'sale_number', 'customer_info', 'total_amount',
        'payment_method_display', 'created_by', 'created_at'
    ]
    list_filter = ['payment_method', 'created_at']
    search_fields = ['sale_number', 'customer_name', 'customer_phone']
    readonly_fields = ['sale_number', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [SaleItemInline]
    list_per_page = 50
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('sale_number', 'total_amount')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone')
        }),
        ('Payment', {
            'fields': ('payment_method', 'mpesa_transaction_id')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_info(self, obj):
        if obj.customer_name:
            return format_html(
                '<strong>{}</strong><br/><small>{}</small>',
                obj.customer_name, obj.customer_phone or 'No phone'
            )
        return format_html('<em>Walk-in Customer</em>')
    customer_info.short_description = 'Customer'
    
    def payment_method_display(self, obj):
        colors = {
            'CASH': '#6c757d',
            'MPESA': '#198754',
            'CARD': '#0dcaf0'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.payment_method, '#6c757d'),
            obj.get_payment_method_display()
        )
    payment_method_display.short_description = 'Payment'


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['sale__created_at']
    search_fields = ['sale__sale_number', 'product__name']