from decimal import Decimal
from rest_framework import status
from rest_framework.test import APITestCase
from shipping.models import Box, Order, OrderItem, Product


class ShippingAPITests(APITestCase):
    def setUp(self):
        self.box = Box.objects.create(
            name="Standard Box",
            inner_length=Decimal("30.00"),
            inner_width=Decimal("20.00"),
            inner_height=Decimal("15.00"),
            max_weight=Decimal("5000.00"),
            cost=Decimal("2.00"),
        )
        self.product = Product.objects.create(
            name="Wireless Headphones",
            sku="AUDIO-001",
            length=Decimal("18.00"),
            width=Decimal("15.00"),
            height=Decimal("8.00"),
            weight=Decimal("350.00"),
        )

    def test_create_product_api(self):
        payload = {
            "name": "Smart Watch",
            "sku": "WATCH-002",
            "length": "10.00",
            "width": "8.00",
            "height": "5.00",
            "weight": "120.00",
        }
        response = self.client.post("/api/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_create_box_api(self):
        payload = {
            "name": "Small Pouch",
            "inner_length": "15.00",
            "inner_width": "10.00",
            "inner_height": "5.00",
            "max_weight": "500.00",
            "cost": "0.50",
        }
        response = self.client.post("/api/boxes/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Box.objects.count(), 2)

    def test_create_order_with_items_api(self):
        payload = {
            "status": "pending",
            "items": [
                {"product_id": self.product.id, "quantity": 2},
            ],
        }
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(OrderItem.objects.first().quantity, 2)

    def test_order_box_recommendation_endpoint(self):
        order = Order.objects.create()
        OrderItem.objects.create(order=order, product=self.product, quantity=1)

        response = self.client.get(f"/api/orders/{order.id}/recommend-box/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["strategy"], "single_box")
        self.assertEqual(data["total_boxes"], 1)
        self.assertEqual(data["boxes"][0]["box_id"], self.box.id)
        self.assertEqual(data["total_cost"], 2.0)

    def test_ad_hoc_box_recommendation_endpoint(self):
        payload = {
            "items": [
                {
                    "name": "Custom Widget",
                    "sku": "CUSTOM-WIDGET",
                    "length": "12.0",
                    "width": "10.0",
                    "height": "5.0",
                    "weight": "200.0",
                    "quantity": 2,
                }
            ]
        }
        response = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["strategy"], "single_box")
        self.assertEqual(data["boxes"][0]["box_id"], self.box.id)

    def test_ad_hoc_box_recommendation_with_product_id(self):
        payload = {
            "items": [
                {
                    "product_id": self.product.id,
                    "quantity": 1,
                }
            ]
        }
        response = self.client.post("/api/recommend-box/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["success"])

    def test_recommendation_for_nonexistent_order_returns_404(self):
        response = self.client.get("/api/orders/99999/recommend-box/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
