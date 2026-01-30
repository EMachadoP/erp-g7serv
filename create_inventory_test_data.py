import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from estoque.models import Product, StockMovement

def create_inventory_data():
    # Create Products
    products_data = [
        {'name': 'Produto A', 'sku': 'PROD-A', 'cost': 50.00, 'sale': 100.00, 'min': 10},
        {'name': 'Produto B', 'sku': 'PROD-B', 'cost': 30.00, 'sale': 60.00, 'min': 20},
        {'name': 'Produto C', 'sku': 'PROD-C', 'cost': 80.00, 'sale': 150.00, 'min': 5},
    ]

    for data in products_data:
        product, created = Product.objects.get_or_create(
            sku=data['sku'],
            defaults={
                'name': data['name'],
                'cost_price': data['cost'],
                'sale_price': data['sale'],
                'minimum_stock': data['min'],
                'current_stock': 0
            }
        )
        if created:
            print(f"Product created: {product}")
        else:
            print(f"Product already exists: {product}")

        # Initial Stock Movement
        StockMovement.objects.create(
            product=product,
            movement_type='IN',
            quantity=data['min'] * 2,
            reason='Estoque Inicial'
        )
        print(f"Initial stock added for {product}")

if __name__ == '__main__':
    create_inventory_data()
