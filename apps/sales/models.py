from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
# from decimal import Decimal

# Create your models here.
class Sale(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('MPESA', 'M-Pesa'),
        ('CARD', 'Card'),
    ]
    
    sale_number = models.CharField(max_length=50, unique=True, editable=False)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='CASH')
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['sale_number']),
        ]
    
    def __str__(self):
        return f"Sale {self.sale_number} - KES {self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.sale_number:
            # Generate sale number: SALE-YYYYMMDD-XXXX
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(sale_number__startswith=f'SALE-{date_str}').order_by('-sale_number').first()
            if last_sale:
                last_num = int(last_sale.sale_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.sale_number = f'SALE-{date_str}-{new_num:04d}'
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)