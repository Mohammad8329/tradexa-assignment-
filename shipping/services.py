"""
Shipping box recommendation and packaging optimization engine.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet
from shipping.models import Box, Order, OrderItem, Product


@dataclass
class PackedItem:
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_weight: Decimal
    unit_volume: Decimal
    total_weight: Decimal
    total_volume: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sku": self.sku,
            "quantity": self.quantity,
            "unit_weight_g": float(self.unit_weight),
            "unit_volume_cm3": float(self.unit_volume),
            "total_weight_g": float(self.total_weight),
            "total_volume_cm3": float(self.total_volume),
        }


@dataclass
class BoxAssignment:
    box: Box
    items: List[PackedItem] = field(default_factory=list)
    packed_weight: Decimal = Decimal("0.00")
    packed_volume: Decimal = Decimal("0.00")

    @property
    def cost(self) -> Decimal:
        return self.box.cost

    @property
    def weight_utilization_pct(self) -> float:
        if self.box.max_weight <= Decimal("0.00"):
            return 0.0
        return round(float((self.packed_weight / self.box.max_weight) * Decimal("100.0")), 2)

    @property
    def volume_utilization_pct(self) -> float:
        if self.box.volume <= Decimal("0.00"):
            return 0.0
        return round(float((self.packed_volume / self.box.volume) * Decimal("100.0")), 2)

    def can_fit_unit(self, product: Product) -> bool:
        """Check if an additional product unit fits into the box's remaining capacity."""
        if (self.packed_weight + product.weight) > self.box.max_weight:
            return False
        if (self.packed_volume + product.volume) > self.box.volume:
            return False
        if not self.box.can_accommodate_item_geometry(product.sorted_dimensions):
            return False
        return True

    def add_unit(self, product: Product):
        """Add a single unit of a product into this box."""
        self.packed_weight += product.weight
        self.packed_volume += product.volume
        
        # Check if product is already in the item list to aggregate quantity
        for item in self.items:
            if item.product_id == product.id:
                item.quantity += 1
                item.total_weight += product.weight
                item.total_volume += product.volume
                return

        self.items.append(
            PackedItem(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                quantity=1,
                unit_weight=product.weight,
                unit_volume=product.volume,
                total_weight=product.weight,
                total_volume=product.volume,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "box_id": self.box.id,
            "box_name": self.box.name,
            "box_dimensions_cm": {
                "length": float(self.box.inner_length),
                "width": float(self.box.inner_width),
                "height": float(self.box.inner_height),
            },
            "box_max_weight_g": float(self.box.max_weight),
            "box_cost": float(self.box.cost),
            "packed_weight_g": float(self.packed_weight),
            "packed_volume_cm3": float(self.packed_volume),
            "weight_utilization_pct": self.weight_utilization_pct,
            "volume_utilization_pct": self.volume_utilization_pct,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class RecommendationResult:
    success: bool
    strategy: str  # 'single_box', 'multi_box', or 'none'
    assignments: List[BoxAssignment] = field(default_factory=list)
    total_cost: Decimal = Decimal("0.00")
    total_boxes: int = 0
    total_order_weight: Decimal = Decimal("0.00")
    total_order_volume: Decimal = Decimal("0.00")
    message: str = ""
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "strategy": self.strategy,
            "total_boxes": self.total_boxes,
            "total_cost": float(self.total_cost),
            "total_order_weight_g": float(self.total_order_weight),
            "total_order_volume_cm3": float(self.total_order_volume),
            "message": self.message,
            "errors": self.errors,
            "boxes": [assignment.to_dict() for assignment in self.assignments],
        }


class BoxRecommendationService:
    """
    Service responsible for determining the optimal box or set of boxes for an order.
    """

    @classmethod
    def recommend_for_order(
        cls,
        order: Order,
        available_boxes: Optional[QuerySet[Box]] = None,
    ) -> RecommendationResult:
        """
        Calculates optimal box recommendation for a given Order instance.
        """
        items = list(order.items.select_related("product").all())
        return cls.recommend_for_items(items=items, available_boxes=available_boxes)

    @classmethod
    def recommend_for_items(
        cls,
        items: List[OrderItem],
        available_boxes: Optional[QuerySet[Box]] = None,
    ) -> RecommendationResult:
        """
        Pure algorithmic box recommendation given order items and box choices.
        """
        if available_boxes is None:
            available_boxes = Box.objects.all()

        box_catalog = list(available_boxes.order_by("cost", "inner_length"))

        # Edge case: No boxes configured in database
        if not box_catalog:
            return RecommendationResult(
                success=False,
                strategy="none",
                message="No shipping boxes available in the system catalog.",
                errors=["No box catalog records found."],
            )

        # Edge case: Order has no items
        if not items:
            return RecommendationResult(
                success=False,
                strategy="none",
                message="Order contains no items.",
                errors=["Order item list is empty."],
            )

        # Calculate totals
        total_weight = sum((item.total_weight for item in items), Decimal("0.00"))
        total_volume = sum((item.total_volume for item in items), Decimal("0.00"))

        # Check for unboxable individual products
        for item in items:
            product = item.product
            fits_at_least_one = False
            for box in box_catalog:
                if product.weight <= box.max_weight and box.can_accommodate_item_geometry(product.sorted_dimensions):
                    fits_at_least_one = True
                    break
            if not fits_at_least_one:
                return RecommendationResult(
                    success=False,
                    strategy="none",
                    total_order_weight=total_weight,
                    total_order_volume=total_volume,
                    message=f"Product '{product.name}' (SKU: {product.sku}) exceeds dimensions or weight of all available box models.",
                    errors=[
                        f"Product {product.sku} ({product.length}x{product.width}x{product.height} cm, {product.weight}g) cannot fit in any available box."
                    ],
                )

        # Phase 1: Try single box recommendation
        single_box_candidates: List[Box] = []
        for box in box_catalog:
            # 1. Total Weight Gate
            if total_weight > box.max_weight:
                continue
            # 2. Total Volume Gate
            if total_volume > box.volume:
                continue
            # 3. Geometry Fit Gate (All individual items must physically fit)
            can_fit_all_geometries = True
            for item in items:
                if not box.can_accommodate_item_geometry(item.product.sorted_dimensions):
                    can_fit_all_geometries = False
                    break
            if can_fit_all_geometries:
                single_box_candidates.append(box)

        if single_box_candidates:
            # Sort by cost ascending, then by volume ascending (cheapest, then most compact)
            single_box_candidates.sort(key=lambda b: (b.cost, b.volume))
            chosen_box = single_box_candidates[0]

            assignment = BoxAssignment(box=chosen_box)
            for item in items:
                for _ in range(item.quantity):
                    assignment.add_unit(item.product)

            return RecommendationResult(
                success=True,
                strategy="single_box",
                assignments=[assignment],
                total_cost=chosen_box.cost,
                total_boxes=1,
                total_order_weight=total_weight,
                total_order_volume=total_volume,
                message=f"Optimal single box '{chosen_box.name}' selected (Cost: ${chosen_box.cost}).",
            )

        # Phase 2: Multi-box Bin-Packing Heuristic (Threshold exceeded)
        # Flatten all order units into a list of individual Product instances
        all_units: List[Product] = []
        for item in items:
            for _ in range(item.quantity):
                all_units.append(item.product)

        # Sort units descending by volume, then weight (First-Fit Decreasing)
        all_units.sort(key=lambda p: (p.volume, p.weight), reverse=True)

        packed_assignments: List[BoxAssignment] = []

        for unit in all_units:
            # Try to place unit in an existing open box that minimizes leftover space
            placed = False
            # Find best existing box
            best_existing_assignment: Optional[BoxAssignment] = None
            for assignment in packed_assignments:
                if assignment.can_fit_unit(unit):
                    best_existing_assignment = assignment
                    break

            if best_existing_assignment:
                best_existing_assignment.add_unit(unit)
                placed = True
            else:
                # Open a new box: choose the cheapest box that can fit this unit
                suitable_boxes = [b for b in box_catalog if b.max_weight >= unit.weight and b.volume >= unit.volume and b.can_accommodate_item_geometry(unit.sorted_dimensions)]
                suitable_boxes.sort(key=lambda b: (b.cost, b.volume))
                
                if not suitable_boxes:
                    # Should be covered by pre-check, but safeguard
                    return RecommendationResult(
                        success=False,
                        strategy="none",
                        message=f"Cannot allocate box for unit '{unit.name}'.",
                        errors=[f"Unit '{unit.name}' does not fit in any box."],
                    )
                
                new_box = suitable_boxes[0]
                new_assignment = BoxAssignment(box=new_box)
                new_assignment.add_unit(unit)
                packed_assignments.append(new_assignment)
                placed = True

        total_multi_cost = sum((a.cost for a in packed_assignments), Decimal("0.00"))

        return RecommendationResult(
            success=True,
            strategy="multi_box",
            assignments=packed_assignments,
            total_cost=total_multi_cost,
            total_boxes=len(packed_assignments),
            total_order_weight=total_weight,
            total_order_volume=total_volume,
            message=f"Threshold exceeded for single box. Multi-box recommendation packed items across {len(packed_assignments)} boxes (Total Cost: ${total_multi_cost}).",
        )
