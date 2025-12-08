from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

# Create your models here.
class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('RETURN', 'Return'),
    ]
    
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reference = models.CharField(max_length=100, blank=True, help_text="PO number, sale number, etc.")
    notes = models.TextField(blank=True)
    
    # Stock levels at time of movement
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['movement_type']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"