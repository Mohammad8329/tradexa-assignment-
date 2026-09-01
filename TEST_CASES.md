# Test Cases Specification & Verification Matrix

This document provides a human-readable mapping of all automated test cases implemented in the Shipping Box Recommendation Engine test suite (`shipping/tests/`).

- **Total Test Cases**: 21
- **Passing**: 21
- **Failing**: 0
- **Pass Rate**: 100%

---

## 1. Data Models & Validation (`test_models.py`)

| Test Case ID | Test Method | Plain-English Description | Sample Input | Expected Output | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-MOD-01** | `test_product_creation_and_properties` | Verifies product creation, string representation (`__str__`), volume calculation ($l \times w \times h$), and dimension sorting property. | Product: `Test Book` (SKU: `BOOK-001`)<br>• Length: 20.00 cm<br>• Width: 15.00 cm<br>• Height: 3.00 cm<br>• Weight: 450.00 g | • `str()`: "Test Book (BOOK-001) - 20.00x15.00x3.00 cm, 450.00g"<br>• `volume`: 900.00 cm³<br>• `sorted_dimensions`: [20.00, 15.00, 3.00] | **PASS** |
| **TC-MOD-02** | `test_product_validation` | Validates model validation rules prevent zero/negative dimensions or negative weight via `MinValueValidator`. | Product: `Invalid Dimensions` (SKU: `INV-001`)<br>• Length: 0.00 cm<br>• Width: 10.00 cm<br>• Height: 10.00 cm<br>• Weight: -5.00 g | `ValidationError` raised when calling `full_clean()`. | **PASS** |
| **TC-MOD-03** | `test_box_creation_and_geometry_check` | Verifies box creation, volume calculation, and 3D rotational fit helper (`can_accommodate_item_geometry`). | Box: `Medium Cube` (30x25x20 cm, Max: 5000g)<br>• Item A (sorted): [30, 25, 18] cm<br>• Item B (sorted): [32, 20, 10] cm | • Box `volume`: 15,000.00 cm³<br>• Item A accommodation: `True` (fits)<br>• Item B accommodation: `False` (32 > 30) | **PASS** |
| **TC-MOD-04** | `test_order_and_items_totals` | Verifies aggregate calculation of order item line totals and cumulative order metrics (item count, total weight, total volume). | Order with:<br>• 2x Keyboard (40x15x4 cm, 800g each)<br>• 3x Mouse (10x6x4 cm, 120g each) | • Line 1 total: 1600g, 4800 cm³<br>• Line 2 total: 360g, 720 cm³<br>• Order `total_items_count`: 5<br>• Order `total_weight`: 1960.00 g<br>• Order `total_volume`: 5520.00 cm³ | **PASS** |

---

## 2. Core Box Recommendation Algorithm (`test_services.py`)

*Catalog Baseline for Tests:*
- *Small Box: 20x15x10 cm, Max Weight: 1000g, Cost: $1.00 (Vol: 3,000 cm³)*
- *Medium Box: 30x20x15 cm, Max Weight: 3000g, Cost: $2.50 (Vol: 9,000 cm³)*
- *Large Box: 50x40x30 cm, Max Weight: 10000g, Cost: $5.00 (Vol: 60,000 cm³)*

| Test Case ID | Test Method | Plain-English Description | Sample Input | Expected Output | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-SRV-01** | `test_single_small_item_picks_cheapest_fitting_box` | Verifies that a single small item is packaged in the cheapest qualifying box from the catalog. | Order with 1x Mouse (10x6x4 cm, 150g). | • `success`: `True`<br>• `strategy`: "single_box"<br>• `total_boxes`: 1<br>• Selected Box: "Small Box"<br>• `total_cost`: $1.00 | **PASS** |
| **TC-SRV-02** | `test_item_fitting_by_rotation` | Verifies that 3D rotational geometry allows an item to fit when rotated, even if default dimension ordering seems to exceed one axis. | Order with 1x Rotated Gadget (8x18x12 cm, 500g) tested against Small Box (20x15x10 cm). | • `success`: `True`<br>• Selected Box: "Small Box"<br>(Sorted dims 18x12x8 cm fit within 20x15x10 cm). | **PASS** |
| **TC-SRV-03** | `test_long_item_falls_back_to_larger_box_due_to_dimension` | Verifies that an elongated item with small volume/weight falls back to a larger box when length exceeds small/medium boxes. | Order with 1x Keyboard (45x14x4 cm, 900g, Vol: 2520 cm³). | • `success`: `True`<br>• `strategy`: "single_box"<br>• Selected Box: "Large Box"<br>(45 cm > 20 cm Small, 45 cm > 30 cm Medium). | **PASS** |
| **TC-SRV-04** | `test_weight_capacity_gate` | Verifies that an item fitting volumetrically into small boxes is routed to a larger box when it exceeds box weight capacity. | Order with 1x Heavy Dumbbell (15x10x10 cm, 4500g, Vol: 1500 cm³). | • `success`: `True`<br>• Selected Box: "Large Box"<br>(4500g > 1000g Small, 4500g > 3000g Medium). | **PASS** |
| **TC-SRV-05** | `test_cheapest_box_selected_when_multiple_fit` | Verifies that when multiple boxes can physically accommodate the order, the lowest cost box is selected. | Order with 1x Mouse (10x6x4 cm, 150g).<br>Available: Small Box ($1.00) vs Luxury Small Box ($4.00, identical size). | • `success`: `True`<br>• Selected Box: "Small Box"<br>• `total_cost`: $1.00 | **PASS** |
| **TC-SRV-06** | `test_tie_breaking_picks_smaller_volume` | Verifies that when two candidate boxes have identical cost, the engine selects the more compact box to minimize wasted space. | Order with 1x Tablet (24x18x2 cm, 700g).<br>Available: Medium Box ($2.50, 9000 cm³) vs Medium Compact Box ($2.50, 7500 cm³). | • `success`: `True`<br>• Selected Box: "Medium Compact Box"<br>(7500 cm³ < 9000 cm³). | **PASS** |
| **TC-SRV-07** | `test_unboxable_oversized_item_fails_gracefully` | Verifies graceful failure with clear error feedback when an item exceeds every box in the catalog in dimension or weight. | Order with 1x Giant Sculpture (100x80x70 cm, 50,000g). | • `success`: `False`<br>• Error message contains: "cannot fit in any available box". | **PASS** |
| **TC-SRV-08** | `test_empty_order_returns_failure` | Verifies that passing an empty order without line items returns a descriptive validation failure without throwing exceptions. | Empty Order (0 items). | • `success`: `False`<br>• Message: "Order contains no items." | **PASS** |
| **TC-SRV-09** | `test_no_boxes_in_database` | Verifies system behavior when no shipping boxes are defined in the database catalog. | Order with 1x Mouse, but 0 Box records exist in database. | • `success`: `False`<br>• Message contains: "No shipping boxes available". | **PASS** |
| **TC-SRV-10** | `test_multi_box_recommendation_when_threshold_exceeded` | Verifies that when combined order weight exceeds any single box, multi-box bin packing (First-Fit Decreasing) splits items into multiple boxes. | Order with 4x Heavy Dumbbells (4 x 4500g = 18,000g total weight vs 10,000g max box capacity). | • `success`: `True`<br>• `strategy`: "multi_box"<br>• `total_boxes`: > 1 (2 Large Boxes)<br>• Total packed weight: 18,000.00 g | **PASS** |

---

## 3. REST API Endpoints (`test_api.py`)

| Test Case ID | Test Method | Plain-English Description | Sample Input | Expected Output | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-API-01** | `test_create_product_api` | Verifies `POST /api/products/` creates a new product in the catalog. | `POST /api/products/`<br>`{"name": "Smart Watch", "sku": "WATCH-002", "length": "10.00", "width": "8.00", "height": "5.00", "weight": "120.00"}` | • HTTP 201 Created<br>• Product database count increases to 2 | **PASS** |
| **TC-API-02** | `test_create_box_api` | Verifies `POST /api/boxes/` creates a new box specification in the catalog. | `POST /api/boxes/`<br>`{"name": "Small Pouch", "inner_length": "15.00", "inner_width": "10.00", "inner_height": "5.00", "max_weight": "500.00", "cost": "0.50"}` | • HTTP 201 Created<br>• Box database count increases to 2 | **PASS** |
| **TC-API-03** | `test_create_order_with_items_api` | Verifies `POST /api/orders/` creates an order with nested order line items. | `POST /api/orders/`<br>`{"status": "pending", "items": [{"product_id": 1, "quantity": 2}]}` | • HTTP 201 Created<br>• Order created with 1 line item (qty: 2) | **PASS** |
| **TC-API-04** | `test_order_box_recommendation_endpoint` | Verifies `GET /api/orders/{id}/recommend-box/` computes and returns packaging recommendations for an existing database order. | `GET /api/orders/1/recommend-box/`<br>(Order contains 1x Wireless Headphones: 18x15x8 cm, 350g). | • HTTP 200 OK<br>• `success`: `True`<br>• `strategy`: "single_box"<br>• `total_boxes`: 1<br>• `total_cost`: $2.00 | **PASS** |
| **TC-API-05** | `test_ad_hoc_box_recommendation_endpoint` | Verifies `POST /api/recommend-box/` calculates recommendations for arbitrary custom item manifests without database persistence. | `POST /api/recommend-box/`<br>`{"items": [{"name": "Custom Widget", "sku": "CUSTOM-WIDGET", "length": "12.0", "width": "10.0", "height": "5.0", "weight": "200.0", "quantity": 2}]}` | • HTTP 200 OK<br>• `success`: `True`<br>• `strategy`: "single_box"<br>• Returns recommended Box ID | **PASS** |
| **TC-API-06** | `test_ad_hoc_box_recommendation_with_product_id` | Verifies `POST /api/recommend-box/` calculates recommendations for ad-hoc payloads referencing catalog `product_id`. | `POST /api/recommend-box/`<br>`{"items": [{"product_id": 1, "quantity": 1}]}` | • HTTP 200 OK<br>• `success`: `True` | **PASS** |
| **TC-API-07** | `test_recommendation_for_nonexistent_order_returns_404` | Verifies `GET /api/orders/{id}/recommend-box/` returns 404 Not Found for non-existent order IDs. | `GET /api/orders/99999/recommend-box/` | • HTTP 404 Not Found | **PASS** |
