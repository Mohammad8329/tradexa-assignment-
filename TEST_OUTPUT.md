# Test Suite Execution Output

Ran on: Windows / Python 3.12 / Django 5.2.17 / djangorestframework 3.18.0  
Command: `python manage.py test shipping.tests -v 2`

```text
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 21 test(s).
Operations to perform:
  Synchronize unmigrated apps: messages, rest_framework, staticfiles
  Apply all migrations: admin, auth, contenttypes, sessions, shipping
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying sessions.0001_initial... OK
  Applying shipping.0001_initial... OK
test_ad_hoc_box_recommendation_endpoint (shipping.tests.test_api.ShippingAPITests.test_ad_hoc_box_recommendation_endpoint) ... ok
test_ad_hoc_box_recommendation_with_product_id (shipping.tests.test_api.ShippingAPITests.test_ad_hoc_box_recommendation_with_product_id) ... ok
test_create_box_api (shipping.tests.test_api.ShippingAPITests.test_create_box_api) ... ok
test_create_order_with_items_api (shipping.tests.test_api.ShippingAPITests.test_create_order_with_items_api) ... ok
test_create_product_api (shipping.tests.test_api.ShippingAPITests.test_create_product_api) ... ok
test_order_box_recommendation_endpoint (shipping.tests.test_api.ShippingAPITests.test_order_box_recommendation_endpoint) ... ok
test_recommendation_for_nonexistent_order_returns_404 (shipping.tests.test_api.ShippingAPITests.test_recommendation_for_nonexistent_order_returns_404) ... ok
test_box_creation_and_geometry_check (shipping.tests.test_models.BoxModelTests.test_box_creation_and_geometry_check) ... ok
test_order_and_items_totals (shipping.tests.test_models.OrderModelTests.test_order_and_items_totals) ... ok
test_product_creation_and_properties (shipping.tests.test_models.ProductModelTests.test_product_creation_and_properties) ... ok
test_product_validation (shipping.tests.test_models.ProductModelTests.test_product_validation) ... ok
test_cheapest_box_selected_when_multiple_fit (shipping.tests.test_services.BoxRecommendationServiceTests.test_cheapest_box_selected_when_multiple_fit) ... ok
test_empty_order_returns_failure (shipping.tests.test_services.BoxRecommendationServiceTests.test_empty_order_returns_failure) ... ok
test_item_fitting_by_rotation (shipping.tests.test_services.BoxRecommendationServiceTests.test_item_fitting_by_rotation) ... ok
test_long_item_falls_back_to_larger_box_due_to_dimension (shipping.tests.test_services.BoxRecommendationServiceTests.test_long_item_falls_back_to_larger_box_due_to_dimension) ... ok
test_multi_box_recommendation_when_threshold_exceeded (shipping.tests.test_services.BoxRecommendationServiceTests.test_multi_box_recommendation_when_threshold_exceeded) ... ok
test_no_boxes_in_database (shipping.tests.test_services.BoxRecommendationServiceTests.test_no_boxes_in_database) ... ok
test_single_small_item_picks_cheapest_fitting_box (shipping.tests.test_services.BoxRecommendationServiceTests.test_single_small_item_picks_cheapest_fitting_box) ... ok
test_tie_breaking_picks_smaller_volume (shipping.tests.test_services.BoxRecommendationServiceTests.test_tie_breaking_picks_smaller_volume) ... ok
test_unboxable_oversized_item_fails_gracefully (shipping.tests.test_services.BoxRecommendationServiceTests.test_unboxable_oversized_item_fails_gracefully) ... ok
test_weight_capacity_gate (shipping.tests.test_services.BoxRecommendationServiceTests.test_weight_capacity_gate) ... ok

----------------------------------------------------------------------
Ran 21 tests in 0.080s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
```
