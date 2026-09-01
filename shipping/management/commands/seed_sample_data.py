from decimal import Decimal
from django.core.management.base import BaseCommand
from shipping.models import Box, Order, OrderItem, Product


class Command(BaseCommand):
    help = "Populate database with sample products, boxes, and test orders."

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample products...")
        products_data = [
            {"name": "Wireless Mouse", "sku": "TECH-MOU-001", "length": "12.0", "width": "7.0", "height": "4.0", "weight": "150.0"},
            {"name": "Mechanical Keyboard", "sku": "TECH-KEY-002", "length": "44.0", "width": "14.0", "height": "4.5", "weight": "950.0"},
            {"name": "Coffee Mug", "sku": "HOME-MUG-003", "length": "12.0", "width": "10.0", "height": "11.0", "weight": "380.0"},
            {"name": "27-inch Monitor", "sku": "TECH-MON-004", "length": "62.0", "width": "38.0", "height": "16.0", "weight": "4500.0"},
            {"name": "Hardcover Novel", "sku": "BOOK-NOV-005", "length": "24.0", "width": "16.0", "height": "3.5", "weight": "600.0"},
            {"name": "Running Shoes", "sku": "APPA-SHO-006", "length": "32.0", "width": "20.0", "height": "12.0", "weight": "850.0"},
            {"name": "Cast Iron Skillet", "sku": "KITC-SKI-007", "length": "30.0", "width": "30.0", "height": "6.0", "weight": "3200.0"},
            {"name": "USB-C Cable (Pack of 3)", "sku": "TECH-CAB-008", "length": "15.0", "width": "10.0", "height": "2.0", "weight": "90.0"},
        ]

        products = {}
        for p in products_data:
            obj, created = Product.objects.update_or_create(
                sku=p["sku"],
                defaults={
                    "name": p["name"],
                    "length": Decimal(p["length"]),
                    "width": Decimal(p["width"]),
                    "height": Decimal(p["height"]),
                    "weight": Decimal(p["weight"]),
                },
            )
            products[p["sku"]] = obj
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} Product: {obj.name}")

        self.stdout.write("Seeding sample shipping boxes...")
        boxes_data = [
            {"name": "Small Padded Mailer (Box S-1)", "inner_length": "20.0", "inner_width": "15.0", "inner_height": "5.0", "max_weight": "1000.0", "cost": "0.75"},
            {"name": "Medium Flat Rate Box (Box M-1)", "inner_length": "28.0", "inner_width": "22.0", "inner_height": "14.0", "max_weight": "4000.0", "cost": "1.80"},
            {"name": "Medium Deep Box (Box M-2)", "inner_length": "35.0", "inner_width": "25.0", "inner_height": "20.0", "max_weight": "6000.0", "cost": "2.40"},
            {"name": "Long Mailer Box (Box L-1)", "inner_length": "50.0", "inner_width": "20.0", "inner_height": "10.0", "max_weight": "5000.0", "cost": "2.90"},
            {"name": "Large Heavy-Duty Box (Box L-2)", "inner_length": "50.0", "inner_width": "40.0", "inner_height": "30.0", "max_weight": "15000.0", "cost": "4.50"},
            {"name": "Extra-Large Cargo Box (Box XL-1)", "inner_length": "70.0", "inner_width": "45.0", "inner_height": "25.0", "max_weight": "25000.0", "cost": "7.20"},
        ]

        for b in boxes_data:
            obj, created = Box.objects.update_or_create(
                name=b["name"],
                defaults={
                    "inner_length": Decimal(b["inner_length"]),
                    "inner_width": Decimal(b["inner_width"]),
                    "inner_height": Decimal(b["inner_height"]),
                    "max_weight": Decimal(b["max_weight"]),
                    "cost": Decimal(b["cost"]),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} Box: {obj.name} (${obj.cost})")

        self.stdout.write("Creating demo orders...")
        # Order 1: Small items (Fits in Small Padded Mailer)
        o1 = Order.objects.create(status=Order.Status.PENDING)
        OrderItem.objects.create(order=o1, product=products["TECH-MOU-001"], quantity=1)
        OrderItem.objects.create(order=o1, product=products["TECH-CAB-008"], quantity=1)
        self.stdout.write(f"  Created Order #{o1.id} (Small items: Mouse + Cable)")

        # Order 2: Medium electronics (Fits in Long Mailer or Medium Box)
        o2 = Order.objects.create(status=Order.Status.PENDING)
        OrderItem.objects.create(order=o2, product=products["TECH-KEY-002"], quantity=1)
        OrderItem.objects.create(order=o2, product=products["BOOK-NOV-005"], quantity=1)
        self.stdout.write(f"  Created Order #{o2.id} (Keyboard + Book)")

        # Order 3: Large monitor (Fits in Extra-Large Box)
        o3 = Order.objects.create(status=Order.Status.PENDING)
        OrderItem.objects.create(order=o3, product=products["TECH-MON-004"], quantity=1)
        self.stdout.write(f"  Created Order #{o3.id} (27-inch Monitor)")

        self.stdout.write(self.style.SUCCESS("Successfully seeded sample data!"))
