from decimal import Decimal
from rest_framework import serializers
from shipping.models import Box, Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    volume = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sorted_dimensions = serializers.ListField(
        child=serializers.DecimalField(max_digits=8, decimal_places=2),
        read_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "length",
            "width",
            "height",
            "weight",
            "volume",
            "sorted_dimensions",
        ]


class BoxSerializer(serializers.ModelSerializer):
    volume = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sorted_dimensions = serializers.ListField(
        child=serializers.DecimalField(max_digits=8, decimal_places=2),
        read_only=True,
    )

    class Meta:
        model = Box
        fields = [
            "id",
            "name",
            "inner_length",
            "inner_width",
            "inner_height",
            "max_weight",
            "cost",
            "volume",
            "sorted_dimensions",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    total_weight = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_volume = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "total_weight",
            "total_volume",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_weight = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_volume = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
            "items",
            "total_weight",
            "total_volume",
            "total_items_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class RecommendAdHocItemSerializer(serializers.Serializer):
    """
    Serializer for ad-hoc recommendation calculations without creating a saved database order.
    """
    product_id = serializers.IntegerField(required=False)
    length = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    width = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    height = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    quantity = serializers.IntegerField(default=1, min_value=1)
