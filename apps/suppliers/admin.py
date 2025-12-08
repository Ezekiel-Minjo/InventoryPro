from django.contrib import admin
from .models import Supplier, PurchaseOrder,PurchaseOrderItem
from django.utils.html import format_html
# Register your models here.
# admin.site.register(Supplier)
# admin.site.register(PurchaseOrder)
# admin.site.register(PurchaseOrderItem)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact_person', 'phone_number',
        'email', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'phone_number', 'email']
    ordering = ['name']
    
    fieldsets = (
        ('Supplier Information', {
            'fields': ('name', 'contact_person')
        }),
        ('Contact Details', {
            'fields': ('phone_number', 'email', 'address')
        }),
        ('Additional Info', {
            'fields': ('notes', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ['subtotal']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'status_display',
        'total_amount', 'balance_display', 'expected_date', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'expected_date']
    search_fields = ['po_number', 'supplier__name']
    readonly_fields = ['po_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Purchase Order', {
            'fields': ('po_number', 'supplier', 'status')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'paid_amount')
        }),
        ('Dates', {
            'fields': ('expected_date', 'received_date')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'DRAFT': '#6c757d',
            'SENT': '#0dcaf0',
            'RECEIVED': '#198754',
            'CANCELLED': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def balance_display(self, obj):
        balance = obj.balance
        if balance > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">KES {}</span>',
                balance
            )
        return format_html('<span style="color: #198754;">PAID</span>')
    balance_display.short_description = 'Balance'


