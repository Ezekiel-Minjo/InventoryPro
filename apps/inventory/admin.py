from django.contrib import admin
from .models import StockMovement
from django.utils.html import format_html

# Register your models here.
# admin.site.register(StockMovement)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'movement_type', 'quantity_display',
        'stock_change', 'reference', 'created_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('product', 'movement_type', 'quantity', 'reference', 'notes')
        }),
        ('Stock Levels', {
            'fields': ('stock_before', 'stock_after')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_display(self, obj):
        color = '#198754' if obj.movement_type == 'IN' else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.quantity
        )
    quantity_display.short_description = 'Quantity'
    
    def stock_change(self, obj):
        change = obj.stock_after - obj.stock_before
        if change > 0:
            return format_html(
                '<span style="color: #198754;">+{}</span>',
                change
            )
        elif change < 0:
            return format_html(
                '<span style="color: #dc3545;">{}</span>',
                change
            )
        return '0'
    stock_change.short_description = 'Change'


