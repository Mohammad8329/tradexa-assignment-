from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from shipping.models import Box, Order, OrderItem, Product


class ProductModelTests(TestCase):
    def test_product_creation_and_properties(self):
        product = Product.objects.create(
            name="Test Book",
            sku="BOOK-001",
            length=Decimal("20.00"),
            width=Decimal("15.00"),
            height=Decimal("3.00"),
            weight=Decimal("450.00"),
        )
        self.assertEqual(str(product), "Test Book (BOOK-001) - 20.00x15.00x3.00 cm, 450.00g")
        self.assertEqual(product.volume, Decimal("900.00"))  # 20 * 15 * 3
        self.assertEqual(product.sorted_dimensions, [Decimal("20.00"), Decimal("15.00"), Decimal("3.00")])

    def test_product_validation(self):
        invalid_product = Product(
            name="Invalid Dimensions",
            sku="INV-001",
            length=Decimal("0.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("-5.00"),
        )
        with self.assertRaises(ValidationError):
            invalid_product.full_clean()


class BoxModelTests(TestCase):
    def test_box_creation_and_geometry_check(self):
        box = Box.objects.create(
            name="Medium Cube",
            inner_length=Decimal("30.00"),
            inner_width=Decimal("25.00"),
            inner_height=Decimal("20.00"),
            max_weight=Decimal("5000.00"),
            cost=Decimal("2.50"),
        )
        self.assertEqual(box.volume, Decimal("15000.00"))  # 30 * 25 * 20
        self.assertEqual(box.sorted_dimensions, [Decimal("30.00"), Decimal("25.00"), Decimal("20.00")])

        # Test geometry rotation fit:
        # Product dimensions in different orientation (25 x 30 x 18) -> sorted is 30 x 25 x 18 <= 30 x 25 x 20 -> should fit
        product_sorted = [Decimal("30.00"), Decimal("25.00"), Decimal("18.00")]
        self.assertTrue(box.can_accommodate_item_geometry(product_sorted))

        # Product that exceeds one dimension even after rotation (32 x 20 x 10) -> sorted is 32 x 20 x 10 > 30 on max dim
        product_too_long = [Decimal("32.00"), Decimal("20.00"), Decimal("10.00")]
        self.assertFalse(box.can_accommodate_item_geometry(product_too_long))


class OrderModelTests(TestCase):
    def setUp(self):
        self.prod1 = Product.objects.create(
            name="Keyboard",
            sku="KB-01",
            length=Decimal("40.00"),
            width=Decimal("15.00"),
            height=Decimal("4.00"),
            weight=Decimal("800.00"),
        )
        self.prod2 = Product.objects.create(
            name="Mouse",
            sku="MS-01",
            length=Decimal("10.00"),
            width=Decimal("6.00"),
            height=Decimal("4.00"),
            weight=Decimal("120.00"),
        )

    def test_order_and_items_totals(self):
        order = Order.objects.create()
        item1 = OrderItem.objects.create(order=order, product=self.prod1, quantity=2)
        item2 = OrderItem.objects.create(order=order, product=self.prod2, quantity=3)

        self.assertEqual(item1.total_weight, Decimal("1600.00"))
        self.assertEqual(item1.total_volume, Decimal("4800.00"))  # (40 * 15 * 4) * 2 = 2400 * 2

        self.assertEqual(order.total_items_count, 5)
        self.assertEqual(order.total_weight, Decimal("1960.00"))  # 1600 + 360
        self.assertEqual(order.total_volume, Decimal("5520.00"))  # 4800 + (240 * 3 = 720)
