from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('STK_PUSH', 'Customer Payment (STK Push)'),
        ('B2C', 'Supplier Payment (B2C)'),
        ('REFUND', 'Customer Refund (B2C)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    
    # M-Pesa response fields
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    conversation_id = models.CharField(max_length=100, blank=True)
    originator_conversation_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    result_desc = models.TextField(blank=True)
    
    # Link to sale or purchase order
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('suppliers.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['mpesa_receipt_number']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - KES {self.amount} - {self.status}"