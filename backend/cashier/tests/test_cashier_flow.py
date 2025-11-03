from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from catalog.models import Category, Brand, Product
from people.models import Customer, Seller
from payment.models import PaymentMethod
from stock.models import Stock


User = get_user_model()


class CashierFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_open_movements_close(self):
        # Open with 100
        r = self.client.post("/api/v1/cashier/sessions/open/", {"opening_amount": "100.00"}, format="json")
        assert r.status_code == 201
        sess_id = r.json()["id"]
        # Add inflow 50
        r2 = self.client.post("/api/v1/cashier/movements/", {"type": "INFLOW", "amount": "50.00", "reason": "SUPRIMENTO"}, format="json")
        assert r2.status_code == 201
        # Add outflow 20
        r3 = self.client.post("/api/v1/cashier/movements/", {"type": "OUTFLOW", "amount": "20.00", "reason": "SANGRIA"}, format="json")
        assert r3.status_code == 201
        # Summary should reflect expected 130
        rs = self.client.get("/api/v1/cashier/sessions/current/summary/")
        assert rs.status_code == 200
        s = rs.json()
        assert s["inflow_total"] == "50.00"
        assert s["outflow_total"] == "20.00"
        assert s["expected_amount"] == "130.00"
        assert s["by_reason"]["SUPRIMENTO"]["inflow"] == "50.00"
        assert s["by_reason"]["SANGRIA"]["outflow"] == "20.00"
        # Close with 130
        r4 = self.client.post(f"/api/v1/cashier/sessions/{sess_id}/close/", {"closing_amount": "130.00"}, format="json")
        assert r4.status_code == 200
        data = r4.json()
        assert data["difference"] == "0.00"
        # History summary should contain the session
        rh = self.client.get("/api/v1/cashier/sessions/history/summary/?limit=5")
        assert rh.status_code == 200
        hist = rh.json()
        assert hist["count"] >= 1
        assert any(itm["session_id"] == sess_id for itm in hist["sessions"]) 
        # Filter by user and date
        today = r4.json()["closed_at"][:10]
        rh2 = self.client.get(f"/api/v1/cashier/sessions/history/summary/?user={self.user.id}&date_from={today}&date_to={today}")
        assert rh2.status_code == 200
        hist2 = rh2.json()
        assert hist2["count"] >= 1

    def test_cash_sale_requires_open_session_and_records_inflow(self):
        # seed product and stock
        cat = Category.objects.create(name="A")
        brand = Brand.objects.create(name="B")
        product = Product.objects.create(name="Item", category=cat, brand=brand, cost_price="10.00", margin="10.00")
        Stock.objects.create(product=product, quantity_current=Decimal("5"))
        # seller and customer
        seller_user = User.objects.create_user(username="seller", password="pass1234")
        seller = Seller.objects.create(user=seller_user, name="Vend", access_level="desconto", discount_max=Decimal("10.00"))
        customer = Customer.objects.create(name="Cli", cpf_cnpj="12345678901")
        # method cash (auto settle)
        cash = PaymentMethod.objects.create(code="cash", name="Dinheiro", type="cash", auto_settle=True)
        # create order
        r = self.client.post("/api/v1/sale/orders/", {"seller": seller.id, "customer": customer.id, "payment_method": cash.id}, format="json")
        order_id = r.json()["id"]
        # add item
        self.client.post(f"/api/v1/sale/orders/{order_id}/add-item/", {"product": product.id, "quantity": "1", "unit_price": "100.00"}, format="json")
        # confirm should fail without open session
        r2 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r2.status_code == 400
        # open session and confirm
        self.client.post("/api/v1/cashier/sessions/open/", {"opening_amount": "0.00"}, format="json")
        r3 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r3.status_code == 200
        # movement should exist
        rlist = self.client.get("/api/v1/cashier/movements/")
        assert rlist.status_code == 200
        assert len(rlist.json()) >= 1
