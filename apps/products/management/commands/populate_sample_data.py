"""
Management command to populate sample data
Create this file: apps/products/management/commands/populate_sample_data.py
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random

from apps.products.models import Product, Category
from apps.suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import StockMovement


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            Supplier.objects.all().delete()
            Sale.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))
        
        self.stdout.write('Creating sample data...')
        
        # Get or create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))
        
        # Create Categories
        categories_data = [
            ('Electronics', 'Electronic devices and accessories'),
            ('Groceries', 'Food and beverage items'),
            ('Clothing', 'Apparel and fashion items'),
            ('Books', 'Books and stationery'),
            ('Home & Garden', 'Home improvement and garden supplies'),
            ('Health & Beauty', 'Healthcare and beauty products'),
        ]
        
        categories = {}
        for name, desc in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            categories[name] = category
            if created:
                self.stdout.write(f'Created category: {name}')
        
        # Create Suppliers
        suppliers_data = [
            ('TechSupply Kenya', 'John Doe', '254712345678', 'tech@supply.co.ke'),
            ('FreshFoods Ltd', 'Jane Smith', '254723456789', 'info@freshfoods.co.ke'),
            ('Fashion Hub', 'Mike Johnson', '254734567890', 'sales@fashionhub.co.ke'),
            ('BookWorld Distributors', 'Sarah Wilson', '254745678901', 'orders@bookworld.co.ke'),
        ]
        
        suppliers = []
        for name, contact, phone, email in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact,
                    'phone_number': phone,
                    'email': email,
                    'address': 'Nairobi, Kenya'
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {name}')
        
        # Create Products
        products_data = [
            # Electronics
            ('Samsung Galaxy A14', 'PHONE-001', categories['Electronics'], 18000, 22000, 15, 5),
            ('HP Laptop i5', 'LAPTOP-001', categories['Electronics'], 45000, 55000, 8, 3),
            ('Sony Headphones', 'AUDIO-001', categories['Electronics'], 2500, 3500, 25, 10),
            ('USB Flash Drive 32GB', 'USB-001', categories['Electronics'], 500, 800, 50, 15),
            ('Phone Charger', 'CHAR-001', categories['Electronics'], 300, 600, 100, 20),
            
            # Groceries
            ('Rice 2kg', 'RICE-001', categories['Groceries'], 200, 300, 100, 20),
            ('Cooking Oil 2L', 'OIL-001', categories['Groceries'], 400, 550, 80, 15),
            ('Sugar 1kg', 'SUGAR-001', categories['Groceries'], 120, 180, 150, 30),
            ('Wheat Flour 2kg', 'FLOUR-001', categories['Groceries'], 150, 220, 120, 25),
            ('Tea Leaves 250g', 'TEA-001', categories['Groceries'], 180, 250, 90, 20),
            
            # Clothing
            ('Men\'s T-Shirt', 'TSHIRT-M-001', categories['Clothing'], 500, 900, 40, 10),
            ('Women\'s Dress', 'DRESS-W-001', categories['Clothing'], 1200, 2000, 25, 8),
            ('Jeans Pants', 'JEANS-001', categories['Clothing'], 1500, 2500, 30, 10),
            ('Sports Shoes', 'SHOES-001', categories['Clothing'], 2000, 3500, 20, 5),
            
            # Books
            ('Python Programming Book', 'BOOK-PY-001', categories['Books'], 1500, 2200, 15, 5),
            ('Mathematics Textbook', 'BOOK-MATH-001', categories['Books'], 800, 1200, 30, 10),
            ('Notebook A4', 'NOTE-001', categories['Books'], 80, 150, 200, 50),
            ('Pen Set (10pcs)', 'PEN-001', categories['Books'], 100, 200, 150, 30),
            
            # Home & Garden
            ('Garden Hose 20m', 'HOSE-001', categories['Home & Garden'], 800, 1200, 15, 5),
            ('LED Bulb 15W', 'BULB-001', categories['Home & Garden'], 150, 300, 100, 20),
            
            # Health & Beauty
            ('Hand Sanitizer 500ml', 'SANI-001', categories['Health & Beauty'], 200, 350, 80, 15),
            ('Face Mask (50pcs)', 'MASK-001', categories['Health & Beauty'], 400, 650, 50, 10),
        ]
        
        products = []
        for name, sku, category, cost, selling, stock, reorder in products_data:
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': category,
                    'cost_price': Decimal(str(cost)),
                    'selling_price': Decimal(str(selling)),
                    'current_stock': stock,
                    'reorder_level': reorder,
                    'created_by': admin
                }
            )
            products.append(product)
            
            if created:
                # Create initial stock movement
                StockMovement.objects.create(
                    product=product,
                    movement_type='IN',
                    quantity=stock,
                    reference='Initial Stock',
                    notes='Sample data population',
                    stock_before=0,
                    stock_after=stock,
                    created_by=admin
                )
                self.stdout.write(f'Created product: {name}')
        
        # Create some sales
        self.stdout.write('Creating sample sales...')
        payment_methods = ['CASH', 'MPESA', 'CARD']
        
        for i in range(20):
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            sale_date = timezone.now() - timezone.timedelta(days=days_ago)
            
            sale = Sale.objects.create(
                customer_name=f'Customer {i+1}' if random.random() > 0.3 else '',
                customer_phone=f'2547{random.randint(10000000, 99999999)}' if random.random() > 0.5 else '',
                payment_method=random.choice(payment_methods),
                created_by=admin,
                created_at=sale_date
            )
            
            # Add 1-5 items to sale
            total = Decimal('0')
            num_items = random.randint(1, 5)
            sale_products = random.sample(products, min(num_items, len(products)))
            
            for product in sale_products:
                if product.current_stock > 0:
                    quantity = random.randint(1, min(5, product.current_stock))
                    
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=product.selling_price
                    )
                    
                    total += product.selling_price * quantity
                    
                    # Update stock
                    product.current_stock -= quantity
                    product.save()
                    
                    # Record movement
                    StockMovement.objects.create(
                        product=product,
                        movement_type='OUT',
                        quantity=quantity,
                        reference=sale.sale_number,
                        notes=f'Sale {sale.sale_number}',
                        stock_before=product.current_stock + quantity,
                        stock_after=product.current_stock,
                        created_by=admin,
                        created_at=sale_date
                    )
            
            sale.total_amount = total
            sale.save()
        
        self.stdout.write(self.style.SUCCESS('Created 20 sample sales'))
        
        # Create some purchase orders
        self.stdout.write('Creating sample purchase orders...')
        
        for i in range(5):
            po = PurchaseOrder.objects.create(
                supplier=random.choice(suppliers),
                status=random.choice(['DRAFT', 'SENT', 'RECEIVED']),
                expected_date=timezone.now().date() + timezone.timedelta(days=random.randint(1, 30)),
                created_by=admin
            )
            
            # Add items
            total = Decimal('0')
            po_products = random.sample(products, random.randint(2, 5))
            
            for product in po_products:
                quantity = random.randint(10, 50)
                
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity=quantity,
                    unit_cost=product.cost_price
                )
                
                total += product.cost_price * quantity
            
            po.total_amount = total
            po.save()
        
        self.stdout.write(self.style.SUCCESS('Created 5 sample purchase orders'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Sample Data Created ==='))
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Suppliers: {Supplier.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'Sales: {Sale.objects.count()}')
        self.stdout.write(f'Purchase Orders: {PurchaseOrder.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\nAdmin Login:'))
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')


# # Alternative: JSON Fixture
# # fixtures/sample_data.json
# """
# You can also create a JSON fixture file. To generate it from existing data:
# python manage.py dumpdata products.Category products.Product --indent 2 > fixtures/sample_data.json

# To load:
# python manage.py loaddata fixtures/sample_data.json
# """

# SAMPLE_JSON_FIXTURE = """
# [
# {
#     "model": "products.category",
#     "pk": 1,
#     "fields": {
#         "name": "Electronics",
#         "description": "Electronic devices and accessories",
#         "created_at": "2024-01-01T10:00:00Z"
#     }
# },
# {
#     "model": "products.category",
#     "pk": 2,
#     "fields": {
#         "name": "Groceries",
#         "description": "Food and beverage items",
#         "created_at": "2024-01-01T10:00:00Z"
#     }
# },
# {
#     "model": "products.product",
#     "pk": 1,
#     "fields": {
#         "name": "Samsung Galaxy A14",
#         "sku": "PHONE-001",
#         "barcode": "",
#         "category": 1,
#         "description": "Latest Samsung smartphone",
#         "image": "",
#         "cost_price": "18000.00",
#         "selling_price": "22000.00",
#         "current_stock": 15,
#         "reorder_level": 5,
#         "is_active": true,
#         "created_at": "2024-01-01T10:00:00Z",
#         "updated_at": "2024-01-01T10:00:00Z"
#     }
# }
# ]
# """

# # Create another management command for quick demo data
# # apps/products/management/commands/create_demo_user.py
# """
# from django.core.management.base import BaseCommand
# from django.contrib.auth.models import User


# class Command(BaseCommand):
#     help = 'Create a demo user for testing'
    
#     def handle(self, *args, **options):
#         username = 'demo'
#         email = 'demo@example.com'
#         password = 'demo123'
        
#         if User.objects.filter(username=username).exists():
#             self.stdout.write(self.style.WARNING(f'User {username} already exists'))
#             return
        
#         user = User.objects.create_user(
#             username=username,
#             email=email,
#             password=password
#         )
        
#         self.stdout.write(self.style.SUCCESS(f'Demo user created!'))
#         self.stdout.write(f'Username: {username}')
#         self.stdout.write(f'Password: {password}')
# """