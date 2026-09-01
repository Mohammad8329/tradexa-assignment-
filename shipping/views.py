from decimal import Decimal
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from shipping.models import Box, Order, OrderItem, Product
from shipping.serializers import (
    BoxSerializer,
    OrderSerializer,
    ProductSerializer,
)
from shipping.services import BoxRecommendationService


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed, created, edited, or deleted.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BoxViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows shipping box types to be viewed, created, edited, or deleted.
    """
    queryset = Box.objects.all()
    serializer_class = BoxSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows orders to be viewed or created.
    """
    queryset = Order.objects.prefetch_related("items__product").all()
    serializer_class = OrderSerializer

    @action(detail=True, methods=["get", "post"], url_path="recommend-box")
    def recommend_box(self, request, pk=None):
        """
        Calculate and return the optimal shipping box (or multi-box strategy) for this order.
        """
        order = self.get_object()
        result = BoxRecommendationService.recommend_for_order(order)
        
        response_status = status.HTTP_200_OK if result.success else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(result.to_dict(), status=response_status)


class AdHocRecommendationView(APIView):
    """
    Endpoint to test box recommendation for arbitrary items without needing a persisted Order.
    Accepts a list of items with product_id or raw dimensions + weight + quantity.
    """

    def post(self, request):
        items_payload = request.data.get("items", [])
        if not items_payload:
            return Response(
                {"error": "Please provide an 'items' array in request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_items = []
        for idx, raw_item in enumerate(items_payload):
            if "product_id" in raw_item:
                try:
                    product = Product.objects.get(pk=raw_item["product_id"])
                except Product.DoesNotExist:
                    return Response(
                        {"error": f"Product with ID {raw_item['product_id']} not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                # Ephemeral product from direct dimensions
                try:
                    product = Product(
                        name=raw_item.get("name", f"Custom Item #{idx+1}"),
                        sku=raw_item.get("sku", f"CUSTOM-{idx+1}"),
                        length=Decimal(str(raw_item["length"])),
                        width=Decimal(str(raw_item["width"])),
                        height=Decimal(str(raw_item["height"])),
                        weight=Decimal(str(raw_item["weight"])),
                    )
                except (KeyError, ValueError) as e:
                    return Response(
                        {"error": f"Invalid item specification at index {idx}: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            quantity = int(raw_item.get("quantity", 1))
            if quantity < 1:
                return Response(
                    {"error": f"Quantity must be at least 1 for item at index {idx}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Ephemeral order item
            order_item = OrderItem(product=product, quantity=quantity)
            order_items.append(order_item)

        result = BoxRecommendationService.recommend_for_items(items=order_items)
        response_status = status.HTTP_200_OK if result.success else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(result.to_dict(), status=response_status)
