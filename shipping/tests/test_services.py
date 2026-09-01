from decimal import Decimal
from django.test import TestCase
from shipping.models import Box, Order, OrderItem, Product
from shipping.services import BoxRecommendationService


class BoxRecommendationServiceTests(TestCase):
    def setUp(self):
        # Setup standard boxes
        self.box_small = Box.objects.create(
            name="Small Box",
            inner_length=Decimal("20.00"),
            inner_width=Decimal("15.00"),
            inner_height=Decimal("10.00"),
            max_weight=Decimal("1000.00"),
            cost=Decimal("1.00"),
        )  # Vol: 3,000 cm3
        
        self.box_medium = Box.objects.create(
            name="Medium Box",
            inner_length=Decimal("30.00"),
            inner_width=Decimal("20.00"),
            inner_height=Decimal("15.00"),
            max_weight=Decimal("3000.00"),
            cost=Decimal("2.50"),
        )  # Vol: 9,000 cm3

        self.box_large = Box.objects.create(
            name="Large Box",
            inner_length=Decimal("50.00"),
            inner_width=Decimal("40.00"),
            inner_height=Decimal("30.00"),
            max_weight=Decimal("10000.00"),
            cost=Decimal("5.00"),
        )  # Vol: 60,000 cm3

        # Setup standard products
        self.mouse = Product.objects.create(
            name="Mouse",
            sku="MS-01",
            length=Decimal("10.00"),
            width=Decimal("6.00"),
            height=Decimal("4.00"),
            weight=Decimal("150.00"),
        )  # Vol: 240 cm3

        self.keyboard = Product.objects.create(
            name="Keyboard",
            sku="KB-01",
            length=Decimal("45.00"),
            width=Decimal("14.00"),
            height=Decimal("4.00"),
            weight=Decimal("900.00"),
        )  # Vol: 2520 cm3

        self.dumbbell = Product.objects.create(
            name="Heavy Dumbbell",
            sku="DB-01",
            length=Decimal("15.00"),
            width=Decimal("10.00"),
            height=Decimal("10.00"),
            weight=Decimal("4500.00"),
        )  # Vol: 1500 cm3

    def test_single_small_item_picks_cheapest_fitting_box(self):
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.mouse, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.strategy, "single_box")
        self.assertEqual(result.total_boxes, 1)
        self.assertEqual(result.assignments[0].box.id, self.box_small.id)
        self.assertEqual(result.total_cost, Decimal("1.00"))

    def test_item_fitting_by_rotation(self):
        # Product dimensions oriented as (4, 10, 6) should fit into Small Box (20, 15, 10)
        rotated_product = Product.objects.create(
            name="Rotated Gadget",
            sku="ROT-01",
            length=Decimal("8.00"),
            width=Decimal("18.00"),
            height=Decimal("12.00"),
            weight=Decimal("500.00"),
        )
        # Rotated product sorted: (18, 12, 8)
        # Small box sorted: (20, 15, 10) -> 18<=20, 12<=15, 8<=10 -> Fits!
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=rotated_product, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.assignments[0].box.id, self.box_small.id)

    def test_long_item_falls_back_to_larger_box_due_to_dimension(self):
        # Keyboard length 45cm exceeds small box (20cm) and medium box (30cm), requires large box (50cm)
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.keyboard, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.strategy, "single_box")
        self.assertEqual(result.assignments[0].box.id, self.box_large.id)

    def test_weight_capacity_gate(self):
        # Dumbbell fits volume of Small Box (1,500 < 3,000), but weight 4500g exceeds Small (1000g) & Medium (3000g)
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.dumbbell, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.strategy, "single_box")
        self.assertEqual(result.assignments[0].box.id, self.box_large.id)

    def test_cheapest_box_selected_when_multiple_fit(self):
        # Create an alternative premium box with same dimensions as small box but higher cost
        Box.objects.create(
            name="Luxury Small Box",
            inner_length=Decimal("20.00"),
            inner_width=Decimal("15.00"),
            inner_height=Decimal("10.00"),
            max_weight=Decimal("1000.00"),
            cost=Decimal("4.00"),
        )
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.mouse, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        # Must pick the $1.00 box, not the $4.00 box
        self.assertEqual(result.assignments[0].box.id, self.box_small.id)
        self.assertEqual(result.total_cost, Decimal("1.00"))

    def test_tie_breaking_picks_smaller_volume(self):
        # Two boxes with same cost ($2.50) but different volumes
        Box.objects.create(
            name="Medium Compact Box",
            inner_length=Decimal("25.00"),
            inner_width=Decimal("20.00"),
            inner_height=Decimal("15.00"),
            max_weight=Decimal("3000.00"),
            cost=Decimal("2.50"),
        )  # Vol: 7,500 cm3 vs medium box 9,000 cm3
        
        # Product too big for small box, fits in both medium boxes
        item = Product.objects.create(
            name="Tablet",
            sku="TAB-01",
            length=Decimal("24.00"),
            width=Decimal("18.00"),
            height=Decimal("2.00"),
            weight=Decimal("700.00"),
        )
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=item, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.assignments[0].box.name, "Medium Compact Box")

    def test_unboxable_oversized_item_fails_gracefully(self):
        giant_item = Product.objects.create(
            name="Giant Sculpture",
            sku="GIANT-01",
            length=Decimal("100.00"),
            width=Decimal("80.00"),
            height=Decimal("70.00"),
            weight=Decimal("50000.00"),
        )
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=giant_item, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertFalse(result.success)
        self.assertIn("cannot fit in any available box", result.errors[0])

    def test_empty_order_returns_failure(self):
        empty_order = Order.objects.create()
        result = BoxRecommendationService.recommend_for_order(empty_order)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Order contains no items.")

    def test_no_boxes_in_database(self):
        Box.objects.all().delete()
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.mouse, quantity=1)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertFalse(result.success)
        self.assertIn("No shipping boxes available", result.message)

    def test_multi_box_recommendation_when_threshold_exceeded(self):
        # Order with 4 heavy dumbbells (4 * 4500g = 18,000g).
        # Large Box max capacity is 10,000g.
        # Single box cannot fit all items (18,000g > 10,000g).
        # Algorithm should trigger multi_box strategy packing across multiple boxes.
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.dumbbell, quantity=4)

        result = BoxRecommendationService.recommend_for_order(order)
        self.assertTrue(result.success)
        self.assertEqual(result.strategy, "multi_box")
        self.assertGreater(result.total_boxes, 1)
        self.assertEqual(sum(a.packed_weight for a in result.assignments), Decimal("18000.00"))
