# E-Commerce Shipping Box Recommendation Engine

A clean, robust Django & Django REST Framework application that calculates and recommends the most cost-effective and dimensionally suitable shipping box (or multi-box strategy) for customer orders in an ecommerce warehouse.

---

## Features

- **Optimal Box Selection Algorithm**:
  - **Single-Box Strategy**: Finds all boxes that can fit total order weight, total order volume, and individual product 3D geometries (with 3-axis rotation support), ranking candidates to pick the **cheapest** (and smallest among cost ties).
  - **Multi-Box Packing (Threshold Exceeded)**: When order volume or weight exceeds any single box, a First-Fit Decreasing bin-packing heuristic groups items into multiple cost-effective boxes.
- **REST API (Django REST Framework)**:
  - Full CRUD for Products, Boxes, and Orders.
  - Dedicated endpoint `POST /api/orders/{id}/recommend-box/` for persisted orders.
  - Ad-hoc endpoint `POST /api/recommend-box/` for calculating recommendations on raw item payloads without saving to database.
- **Modern Django Admin UI (`django-jazzmin`)**:
  - Customized Bootswatch / AdminLTE interface with dark mode and model icons.
  - Real-time packaging preview badges in the order list.
  - Deep-dive box breakdown with weight & volume capacity utilization percentages.
- **Dedicated Homepage & Custom 404**:
  - Viewport-centered landing page (`/`) with a 3-step visual "How It Works" workflow guide.
  - Themed 404 error page (`templates/404.html`) for production routing.
- **Production-Ready Static Asset Pipeline (`WhiteNoise`)**:
  - Full static file serving with gzip/brotli compression enabled out of the box (`DEBUG = False`).
- **Zero-Setup Database**: Configured with SQLite out of the box.
- **100% Test Coverage for Core Engine**: 21 unit and integration tests covering models, services, rotation, multi-box packing, and API endpoints.
- **Continuous Integration**: GitHub Actions CI workflow configured for automated multi-version Python testing.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.11 or 3.12 recommended)
- `pip` and `virtualenv`

### 2. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd tradexa-assignment-

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Migrations, Collect Static & Seed Sample Data

```bash
# Apply migrations
python manage.py migrate

# Collect static assets for WhiteNoise
python manage.py collectstatic --noinput

# Populate sample products, boxes, and test orders
python manage.py seed_sample_data
```

### 4. Create Superuser & Run Development Server

```bash
# Create admin user (interactive)
python manage.py createsuperuser

# Start the dev server
python manage.py runserver
```

### 5. Access Points
- **Homepage & Workflow Guide**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Dashboard**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Browsable REST API**: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

---

## Running the Tests

To run the automated test suite with verbose output:

```bash
python manage.py test shipping.tests -v 2
```

To view the full human-readable test case matrix and specifications, see [`TEST_CASES.md`](TEST_CASES.md).
To view the raw recorded test execution output, see [`TEST_OUTPUT.md`](TEST_OUTPUT.md).

---

## API Documentation & Examples

### 1. Box Recommendation for an Existing Order
**Endpoint**: `GET` or `POST` `/api/orders/{order_id}/recommend-box/`

**Sample Response**:
```json
{
  "success": true,
  "strategy": "single_box",
  "total_boxes": 1,
  "total_cost": 0.75,
  "total_order_weight_g": 240.0,
  "total_order_volume_cm3": 540.0,
  "message": "Optimal single box 'Small Padded Mailer (Box S-1)' selected (Cost: $0.75).",
  "errors": [],
  "boxes": [
    {
      "box_id": 1,
      "box_name": "Small Padded Mailer (Box S-1)",
      "box_dimensions_cm": {
        "length": 20.0,
        "width": 15.0,
        "height": 5.0
      },
      "box_max_weight_g": 1000.0,
      "box_cost": 0.75,
      "packed_weight_g": 240.0,
      "packed_volume_cm3": 540.0,
      "weight_utilization_pct": 24.0,
      "volume_utilization_pct": 36.0,
      "items": [
        {
          "product_id": 1,
          "product_name": "Wireless Mouse",
          "sku": "TECH-MOU-001",
          "quantity": 1,
          "unit_weight_g": 150.0,
          "unit_volume_cm3": 336.0,
          "total_weight_g": 150.0,
          "total_volume_cm3": 336.0
        },
        {
          "product_id": 8,
          "product_name": "USB-C Cable (Pack of 3)",
          "sku": "TECH-CAB-008",
          "quantity": 1,
          "unit_weight_g": 90.0,
          "unit_volume_cm3": 300.0,
          "total_weight_g": 90.0,
          "total_volume_cm3": 300.0
        }
      ]
    }
  ]
}
```

---

### 2. Ad-Hoc Recommendation (Without saving to DB)
**Endpoint**: `POST /api/recommend-box/`

**Request Body**:
```json
{
  "items": [
    {
      "name": "Custom Mechanical Keyboard",
      "sku": "CUSTOM-KB",
      "length": 44.0,
      "width": 14.0,
      "height": 4.5,
      "weight": 950.0,
      "quantity": 1
    },
    {
      "name": "Coffee Mug",
      "sku": "CUSTOM-MUG",
      "length": 12.0,
      "width": 10.0,
      "height": 11.0,
      "weight": 380.0,
      "quantity": 2
    }
  ]
}
```

Or reference existing product IDs directly:
```json
{
  "items": [
    { "product_id": 1, "quantity": 3 },
    { "product_id": 2, "quantity": 1 }
  ]
}
```

---

### 3. Create a New Order via API
**Endpoint**: `POST /api/orders/`

**Request Body**:
```json
{
  "status": "pending",
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

---

## Project Structure

```text
tradexa-assignment-/
├── manage.py
├── requirements.txt          # Django, DRF, django-jazzmin, whitenoise
├── README.md
├── TEST_CASES.md             # Human-readable test case matrix & specifications
├── TEST_OUTPUT.md            # Raw terminal output from test suite
├── Progress.md               # AI development log & design rationale
├── .gitignore
├── .github/
│   └── workflows/
│       └── tests.yml         # GitHub Actions CI workflow
├── config/
│   ├── __init__.py
│   ├── settings.py           # Jazzmin, WhiteNoise, DRF, and SQLite config
│   ├── urls.py               # Root URL router
│   └── wsgi.py
├── templates/
│   ├── home.html             # Themed landing page & 3-step guide
│   └── 404.html              # Custom themed 404 error page
├── staticfiles/              # Collected static assets for WhiteNoise
└── shipping/
    ├── __init__.py
    ├── admin.py              # Django Admin custom interfaces & packing previews
    ├── apps.py
    ├── models.py             # Product, Box, Order, OrderItem
    ├── serializers.py        # DRF serializers
    ├── services.py           # Core box recommendation & bin-packing algorithm
    ├── urls.py               # API route definitions
    ├── views.py              # DRF ViewSets and recommendation actions
    ├── management/
    │   └── commands/
    │       └── seed_sample_data.py  # Realistic data seeder
    ├── migrations/
    │   └── 0001_initial.py
    └── tests/
        ├── __init__.py
        ├── test_models.py    # Model constraints and properties
        ├── test_services.py  # Algorithmic engine and edge cases
        └── test_api.py       # REST API integration tests
```

---

## CI / CD & Quality Assurance

- **GitHub Actions**: Automated test runner configured in `.github/workflows/tests.yml` to run tests against Python 3.11 and 3.12 on every push/PR.
- **Local Test Output**: The complete execution log is stored in `TEST_OUTPUT.md`.
