from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class CatalogApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        # Obtain token
        resp = self.client.post(
            "/api/token/",
            {"username": "tester", "password": "pass1234"},
            format="json",
        )
        assert resp.status_code == 200, resp.content
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")

    def test_category_brand_product_flow(self):
        # Create category
        r = self.client.post(
            "/api/v1/catalog/categories/",
            {"name": "Eletrônicos"},
            format="json",
        )
        assert r.status_code == 201, r.content
        cat_id = r.json()["id"]

        # Create brand
        r = self.client.post(
            "/api/v1/catalog/brands/",
            {"name": "Acme"},
            format="json",
        )
        assert r.status_code == 201, r.content
        brand_id = r.json()["id"]

        # Create product and ensure sale_price is calculated
        payload = {
            "name": "Fone de Ouvido",
            "description": "Bluetooth",
            "category": cat_id,
            "brand": brand_id,
            "cost_price": "100.00",
            "margin": "25.00",
            "barcode": "1234567890123",
            "active": True,
        }
        r = self.client.post("/api/v1/catalog/products/", payload, format="json")
        assert r.status_code == 201, r.content
        data = r.json()
        assert data["sale_price"] == "125.00"
        assert data["sku"].startswith("P")

        # List product with filters
        r = self.client.get(f"/api/v1/catalog/products/?brand={brand_id}&category={cat_id}&search=Fone&ordering=-sale_price")
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_promotion_validation(self):
        # Setup cat/brand/product
        cat = self.client.post("/api/v1/catalog/categories/", {"name": "A"}, format="json").json()
        brand = self.client.post("/api/v1/catalog/brands/", {"name": "B"}, format="json").json()
        prod = self.client.post(
            "/api/v1/catalog/products/",
            {
                "name": "Item",
                "category": cat["id"],
                "brand": brand["id"],
                "cost_price": "50.00",
                "margin": "10.00",
            },
            format="json",
        ).json()

        # Create active promotion
        r = self.client.post(
            "/api/v1/catalog/promotions/",
            {"product": prod["id"], "percent_off": "10.00", "start_date": "2025-01-01", "end_date": "2025-12-31", "active": True},
            format="json",
        )
        assert r.status_code == 201, r.content

        # Try to create another active promotion for same product -> should fail
        r2 = self.client.post(
            "/api/v1/catalog/promotions/",
            {"product": prod["id"], "percent_off": "5.00", "start_date": "2025-06-01", "end_date": "2025-12-31", "active": True},
            format="json",
        )
        assert r2.status_code == 400
        assert "active" in r2.json()

