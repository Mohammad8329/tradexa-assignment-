# AI Usage & Development Progress Log

This log records the development process, architectural decisions, algorithmic design, and test validation for the Shipping Box Recommendation system.

---

## 1. Requirement Analysis & Planning
- **Problem**: In an ecommerce warehouse environment, recommend the most cost-effective and dimensionally suitable shipping box (or multiple boxes if thresholds are exceeded) for orders containing items with varying length, width, height, and weight.
- **Clarification & Decisions**:
  - **Units**: Metric standard — Centimeters (cm) for length/width/height, Grams (g) for weight.
  - **Threshold / Multi-box Logic**: When an order's combined items exceed the capacity of any single box (or individual item dimensions require splitting), activate a multi-box bin packing algorithm (First-Fit / Best-Fit Decreasing) to group items into the lowest-cost combination of boxes.
  - **Database**: SQLite for lightweight, zero-configuration portability and self-contained execution.
  - **Interface**: Both a REST API (via Django REST Framework) for automated warehouse systems and Django Admin for manual inspection with interactive packaging previews.

---

## 2. Architecture & Data Modeling

### Models (`shipping/models.py`)
1. **`Product`**:
   - Fields: `name`, `sku` (unique), `length`, `width`, `height`, `weight`.
   - Properties: `volume` ($l \times w \times h$), `sorted_dimensions` (descending tuple for 3D rotation invariant matching).
   - Validations: `MinValueValidator` ensures strictly positive dimensions and weight.
2. **`Box`**:
   - Fields: `name`, `inner_length`, `inner_width`, `inner_height`, `max_weight`, `cost`.
   - Properties: `volume`, `sorted_dimensions`.
   - Helper: `can_accommodate_item_geometry(item_sorted_dims)` checks whether an item fits inside the box under any 3D rotation (sorted item dimensions $\le$ sorted box inner dimensions element-wise).
3. **`Order` & `OrderItem`**:
   - Represents the customer order and line items with product foreign keys and quantities.
   - Computes aggregated line and order metrics (`total_weight`, `total_volume`, `total_items_count`).

---

## 3. Algorithmic Design (`shipping/services.py`)

The box selection logic is isolated in a pure service layer (`BoxRecommendationService`) rather than embedded in views or models.

### Algorithm Flow:
1. **Sanity / Gate Check**:
   - Check if any individual product is strictly unboxable (i.e. exceeds the maximum weight or dimensional envelope of every box in the catalog). If so, fail early with a clear descriptive message.
2. **Phase 1: Single-Box Candidate Search**:
   - Evaluates all available boxes:
     1. `total_order_weight <= box.max_weight`
     2. `total_order_volume <= box.volume`
     3. Every item's 3D geometry fits within the box's dimensions.
   - If candidates exist, sort candidates by `cost ASC`, then `volume ASC` (cheapest first, breaking ties with the most compact box).
   - Returns a single-box recommendation.
3. **Phase 2: Multi-Box Packing (Threshold Exceeded)**:
   - If no single box can hold the entire order:
     - Unroll order items into discrete units.
     - Sort units in descending order by volume and weight (First-Fit Decreasing heuristic).
     - Try placing each unit into an existing open box with available capacity.
     - If no open box can accept the unit, open the cheapest new box capable of holding it.
   - Returns detailed breakdown of each box, items inside, utilized weight/volume percentages, and total shipping cost.

---

## 4. API & Interface Implementation

### Endpoints (`shipping/views.py` + `shipping/urls.py`):
- `GET /api/products/`, `POST /api/products/` — Manage product catalog.
- `GET /api/boxes/`, `POST /api/boxes/` — Manage box catalog.
- `GET /api/orders/`, `POST /api/orders/` — Create orders with nested line items.
- `GET /api/orders/{id}/recommend-box/` / `POST /api/orders/{id}/recommend-box/` — Run box recommendation for an existing order.
- `POST /api/recommend-box/` — Ad-hoc recommendation endpoint accepting arbitrary JSON item manifests without requiring database persistence.

### Django Admin (`shipping/admin.py`):
- Custom admin for `Product`, `Box`, and `Order`.
- Tabular inline for line items with real-time display of unit & total weights and volumes.
- Color-coded packaging recommendation preview directly in the Order list view.
- Detailed box-by-box breakdown and space/weight utilization indicators inside the Order detail view.

---

## 5. Testing & Verification

Comprehensive test suites covering:
- **`test_models.py`**: Model validations, geometry checks, volume and weight calculations.
- **`test_services.py`**: 10 distinct algorithmic scenarios (single item, rotation matching, dimension gates, weight gates, cost prioritization, tie breaking, unboxable items, empty orders, multi-box packing).
- **`test_api.py`**: Product/Box/Order CRUD, order recommendation endpoints, and ad-hoc calculation endpoints.

**Result**: 21/21 tests passing in 0.080s. Full terminal output saved in `TEST_OUTPUT.md`.

---

## 6. Continuous Integration & Delivery
- **GitHub Actions (`.github/workflows/tests.yml`)**: Multi-version Python CI (3.11, 3.12) running migrations and tests automatically on push and PR.
- **Local Test Output (`TEST_OUTPUT.md`)**: Verified execution log for immediate reference.
- **Management Command (`seed_sample_data`)**: Single-command database seeding for quick demonstration.
