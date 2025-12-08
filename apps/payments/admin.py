from django.contrib import admin
from .models import Transaction
from django.utils.html import format_html
# Register your models here.
# admin.site.register(Transaction)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_type', 'amount', 'phone_number',
        'status_display', 'mpesa_receipt_number', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = [
        'phone_number', 'mpesa_receipt_number',
        'merchant_request_id', 'checkout_request_id'
    ]
    readonly_fields = [
        'merchant_request_id', 'checkout_request_id',
        'mpesa_receipt_number', 'conversation_id',
        'originator_conversation_id', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_type', 'amount', 'phone_number', 'status')
        }),
        ('M-Pesa Response', {
            'fields': (
                'merchant_request_id', 'checkout_request_id',
                'mpesa_receipt_number', 'conversation_id',
                'originator_conversation_id', 'result_desc'
            )
        }),
        ('Related Records', {
            'fields': ('sale', 'purchase_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'PENDING': '#ffc107',
            'SUCCESS': '#198754',
            'FAILED': '#dc3545',
            'CANCELLED': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


