from django.contrib import admin
from django.utils.html import format_html
from shipping.models import Box, Order, OrderItem, Product
from shipping.services import BoxRecommendationService


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("product", "quantity", "unit_weight_display", "unit_dimensions_display", "total_weight_display", "total_volume_display")
    readonly_fields = ("unit_weight_display", "unit_dimensions_display", "total_weight_display", "total_volume_display")

    @admin.display(description="Unit Weight")
    def unit_weight_display(self, obj):
        return f"{obj.product.weight} g" if obj.product else "-"

    @admin.display(description="Unit Dimensions (LxWxH)")
    def unit_dimensions_display(self, obj):
        return f"{obj.product.length}x{obj.product.width}x{obj.product.height} cm" if obj.product else "-"

    @admin.display(description="Line Total Weight")
    def total_weight_display(self, obj):
        return f"{obj.total_weight} g" if obj.product else "-"

    @admin.display(description="Line Total Volume")
    def total_volume_display(self, obj):
        return f"{obj.total_volume:.1f} cm³" if obj.product else "-"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "dimensions_display", "weight_display", "volume_display")
    search_fields = ("name", "sku")
    list_filter = ()

    @admin.display(description="Dimensions (LxWxH)")
    def dimensions_display(self, obj):
        return f"{obj.length} x {obj.width} x {obj.height} cm"

    @admin.display(description="Weight")
    def weight_display(self, obj):
        return f"{obj.weight} g"

    @admin.display(description="Volume")
    def volume_display(self, obj):
        return f"{obj.volume:.1f} cm³"


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("name", "inner_dimensions_display", "max_weight_display", "volume_display", "cost_display")
    search_fields = ("name",)
    list_filter = ()

    @admin.display(description="Inner Dimensions (LxWxH)")
    def inner_dimensions_display(self, obj):
        return f"{obj.inner_length} x {obj.inner_width} x {obj.inner_height} cm"

    @admin.display(description="Max Weight")
    def max_weight_display(self, obj):
        return f"{obj.max_weight} g"

    @admin.display(description="Internal Volume")
    def volume_display(self, obj):
        return f"{obj.volume:.1f} cm³"

    @admin.display(description="Cost")
    def cost_display(self, obj):
        return f"${obj.cost}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "items_count_display", "total_weight_display", "total_volume_display", "recommendation_preview", "created_at")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "updated_at", "total_weight_display", "total_volume_display", "recommendation_details")

    @admin.display(description="Item Count")
    def items_count_display(self, obj):
        return f"{obj.total_items_count} units"

    @admin.display(description="Total Weight")
    def total_weight_display(self, obj):
        return f"{obj.total_weight} g"

    @admin.display(description="Total Volume")
    def total_volume_display(self, obj):
        return f"{obj.total_volume:.1f} cm³"

    @admin.display(description="Recommended Box")
    def recommendation_preview(self, obj):
        if not obj.items.exists():
            return "No items"
        result = BoxRecommendationService.recommend_for_order(obj)
        if not result.success:
            return format_html('<span style="color: red;">No fitting box</span>')
        if result.strategy == "single_box":
            box = result.assignments[0].box
            return format_html('<span style="color: green; font-weight: bold;">{} (${})</span>', box.name, box.cost)
        return format_html('<span style="color: orange; font-weight: bold;">Multi-box ({} boxes, ${})</span>', result.total_boxes, result.total_cost)

    @admin.display(description="Packaging Recommendation Details")
    def recommendation_details(self, obj):
        if not obj.pk or not obj.items.exists():
            return "Save order items to view recommendation."
        result = BoxRecommendationService.recommend_for_order(obj)
        if not result.success:
            return format_html('<p style="color: red;"><strong>Packaging Failed:</strong> {}</p>', result.message)

        html = [f"<div><strong>Strategy:</strong> {result.strategy.replace('_', ' ').title()}</div>"]
        html.append(f"<div><strong>Total Packaging Cost:</strong> ${result.total_cost}</div>")
        html.append(f"<div><strong>Total Boxes Required:</strong> {result.total_boxes}</div><hr/>")

        for idx, assignment in enumerate(result.assignments, 1):
            box = assignment.box
            html.append(
                f"<div style='margin-bottom: 12px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;'>"
                f"<strong>Box #{idx}: {box.name}</strong> (${box.cost})<br/>"
                f"Dimensions: {box.inner_length}x{box.inner_width}x{box.inner_height} cm | Capacity: {box.max_weight}g<br/>"
                f"Utilized Weight: {assignment.packed_weight}g ({assignment.weight_utilization_pct}%) | "
                f"Utilized Volume: {assignment.packed_volume:.1f} cm³ ({assignment.volume_utilization_pct}%)<br/>"
                f"<em>Packed Items:</em> " + ", ".join([f"{item.quantity}x {item.product_name}" for item in assignment.items]) +
                f"</div>"
            )
        return format_html("".join(html))
