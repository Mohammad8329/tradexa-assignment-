from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """
    Represents an ecommerce product with physical dimensions and weight.
    Dimensions are stored in centimeters (cm) and weight in grams (g).
    """
    name = models.CharField(max_length=120, help_text="Product name/title")
    sku = models.CharField(max_length=64, unique=True, help_text="Unique Stock Keeping Unit")
    length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Length in centimeters (cm)",
    )
    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Width in centimeters (cm)",
    )
    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Height in centimeters (cm)",
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Weight in grams (g)",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.length}x{self.width}x{self.height} cm, {self.weight}g"

    @property
    def volume(self) -> Decimal:
        """Volume in cubic centimeters (cm^3)."""
        return self.length * self.width * self.height

    @property
    def sorted_dimensions(self) -> list[Decimal]:
        """Dimensions sorted descending to allow 3D rotation matching."""
        return sorted([self.length, self.width, self.height], reverse=True)


class Box(models.Model):
    """
    Represents an available shipping packaging box with internal dimensions,
    maximum payload capacity, and packaging cost.
    """
    name = models.CharField(max_length=120, help_text="Box name or model code")
    inner_length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Usable inner length in centimeters (cm)",
    )
    inner_width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Usable inner width in centimeters (cm)",
    )
    inner_height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Usable inner height in centimeters (cm)",
    )
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Maximum weight capacity in grams (g)",
    )
    cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cost per box in standard currency units",
    )

    class Meta:
        ordering = ["cost", "inner_length"]
        verbose_name = "Shipping Box"
        verbose_name_plural = "Shipping Boxes"

    def __str__(self):
        return f"{self.name} [{self.inner_length}x{self.inner_width}x{self.inner_height} cm, max {self.max_weight}g, ${self.cost}]"

    @property
    def volume(self) -> Decimal:
        """Internal volume in cubic centimeters (cm^3)."""
        return self.inner_length * self.inner_width * self.inner_height

    @property
    def sorted_dimensions(self) -> list[Decimal]:
        """Usable inner dimensions sorted descending for 3D rotation checks."""
        return sorted([self.inner_length, self.inner_width, self.inner_height], reverse=True)

    def can_accommodate_item_geometry(self, item_sorted_dims: list[Decimal]) -> bool:
        """Checks if a single item's geometry can fit inside this box under any rotation."""
        box_dims = self.sorted_dimensions
        return all(item_d <= box_d for item_d, box_d in zip(item_sorted_dims, box_dims))


class Order(models.Model):
    """
    Represents a customer order containing one or more product line items.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        BOXED = "boxed", "Boxed"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.pk} [{self.get_status_display()}] ({self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'New'})"

    @property
    def total_weight(self) -> Decimal:
        """Total weight of all items in grams."""
        return sum((item.total_weight for item in self.items.all()), Decimal("0.00"))

    @property
    def total_volume(self) -> Decimal:
        """Total volume of all items in cm^3."""
        return sum((item.total_volume for item in self.items.all()), Decimal("0.00"))

    @property
    def total_items_count(self) -> int:
        """Total count of units across all order items."""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """
    Represents a specific product line item and quantity within an Order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity of this product",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order_id})"

    @property
    def total_weight(self) -> Decimal:
        return self.product.weight * self.quantity

    @property
    def total_volume(self) -> Decimal:
        return self.product.volume * self.quantity
