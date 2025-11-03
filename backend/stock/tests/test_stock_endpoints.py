from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from catalog.models import Category, Brand, Product


User = get_user_model()


class StockApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Create product
        cat = Category.objects.create(name="Eletrônicos")
        brand = Brand.objects.create(name="MarcaX")
        self.product = Product.objects.create(
            name="Cabo",
            category=cat,
            brand=brand,
            cost_price="10.00",
            margin="10.00",
        )

    def test_movements_and_status(self):
        # Set min/max via stock endpoint (created on first movement)
        # Entrada 3 -> ZERADO moves to ABAIXO (min 5)
        r = self.client.post(
            "/api/v1/stock/movements/",
            {"product": self.product.id, "type": "ENTRADA", "quantity": "3"},
            format="json",
        )
        assert r.status_code == 201, r.content

        # Update thresholds
        # Get stock id
        list_resp = self.client.get(f"/api/v1/stock/?product={self.product.id}").json()
        stock_id = list_resp["results"][0]["id"] if isinstance(list_resp, dict) and "results" in list_resp else list_resp[0]["id"]

        r2 = self.client.patch(
            f"/api/v1/stock/{stock_id}/",
            {"minimum": "5", "maximum": "20"},
            format="json",
        )
        assert r2.status_code == 200, r2.content
        assert r2.json()["status"] in ("ABAIXO", "ZERADO")

        # Entrada mais 7 -> total 10 => OK
        r3 = self.client.post(
            "/api/v1/stock/movements/",
            {"product": self.product.id, "type": "ENTRADA", "quantity": "7"},
            format="json",
        )
        assert r3.status_code == 201
        det = self.client.get(f"/api/v1/stock/{stock_id}/").json()
        assert det["quantity_current"] == "10.000"
        assert det["status"] == "OK"

        # Entrada 20 -> total 30 => ACIMA
        r4 = self.client.post(
            "/api/v1/stock/movements/",
            {"product": self.product.id, "type": "ENTRADA", "quantity": "20"},
            format="json",
        )
        assert r4.status_code == 201
        det = self.client.get(f"/api/v1/stock/{stock_id}/").json()
        assert det["status"] == "ACIMA"

    def test_prevent_negative_stock(self):
        # Entrada 5
        r = self.client.post(
            "/api/v1/stock/movements/",
            {"product": self.product.id, "type": "ENTRADA", "quantity": "5"},
            format="json",
        )
        assert r.status_code == 201
        # Saída 10 -> deve falhar (estoque negativo)
        r2 = self.client.post(
            "/api/v1/stock/movements/",
            {"product": self.product.id, "type": "SAIDA", "quantity": "10"},
            format="json",
        )
        assert r2.status_code == 400

