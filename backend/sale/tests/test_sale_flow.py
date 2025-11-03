from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from catalog.models import Category, Brand, Product, Promotion
from people.models import Customer, Seller
from stock.models import Stock
from payment.models import PaymentMethod, Receivable


User = get_user_model()


class SaleFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        cat = Category.objects.create(name="A")
        brand = Brand.objects.create(name="B")
        self.product = Product.objects.create(
            name="Item",
            category=cat,
            brand=brand,
            cost_price=Decimal("100.00"),
            margin=Decimal("10.00"),
        )
        # Seed stock
        Stock.objects.create(product=self.product, quantity_current=Decimal("10"))

        # Seller with 10% cap
        self.seller_user = User.objects.create_user(username="seller", password="pass1234")
        self.seller = Seller.objects.create(user=self.seller_user, name="Vend", access_level="desconto", discount_max=Decimal("10.00"))
        self.customer = Customer.objects.create(name="Cli", cpf_cnpj="12345678901")

    def test_discount_cap_and_price_floor(self):
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id},
            format="json",
        )
        assert r.status_code == 201, r.content
        order_id = r.json()["id"]

        # Try to add item with discount 50% (cap 10% should apply)
        r2 = self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {
                "product": self.product.id,
                "quantity": "2",
                "unit_price": "150.00",
                "discount_percent": "50.00",
            },
            format="json",
        )
        assert r2.status_code == 201, r2.content
        item = r2.json()
        # Cap to 10% then check price floor (MIN_MARGIN_PERCENT default 0 keeps floor at cost)
        assert item["discount_percent"] == "10.00"

    def test_promotion_beats_manual_discount_and_confirm_stock(self):
        # Promotion 15%
        Promotion.objects.create(product=self.product, percent_off=Decimal("15.00"), start_date="2025-01-01", end_date="2099-01-01", active=True)
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id},
            format="json",
        )
        order_id = r.json()["id"]
        # Set payment method to allow confirmation
        pm = PaymentMethod.objects.create(code="pix", name="PIX", type="pix")
        self.client.patch(f"/api/v1/sale/orders/{order_id}/", {"payment_method": pm.id}, format="json")
        # Add item with discount 10% -> promotion 15% wins
        r2 = self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {
                "product": self.product.id,
                "quantity": "3",
                "unit_price": "200.00",
                "discount_percent": "10.00",
            },
            format="json",
        )
        assert r2.status_code == 201
        assert r2.json()["discount_percent"] == "15.00"

        # Confirm order -> stock decreases
        r3 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r3.status_code == 200
        # Stock should be 7 now
        st = Stock.objects.get(product=self.product)
        assert str(st.quantity_current) == "7.000"

    def test_set_payment_method_on_order(self):
        pm = PaymentMethod.objects.create(code="pix", name="PIX", type="pix")
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id},
            format="json",
        )
        order_id = r.json()["id"]
        # Patch to set payment_method
        r2 = self.client.patch(
            f"/api/v1/sale/orders/{order_id}/",
            {"payment_method": pm.id},
            format="json",
        )
        assert r2.status_code == 200, r2.content
        assert r2.json()["payment_method"] == pm.id

    def test_confirm_creates_receivable(self):
        pm = PaymentMethod.objects.create(code="card", name="Cartão Crédito", type="card_credit", settlement_days=30)
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id, "payment_method": pm.id},
            format="json",
        )
        order_id = r.json()["id"]
        # Add item
        r2 = self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {"product": self.product.id, "quantity": "1", "unit_price": "200.00"},
            format="json",
        )
        assert r2.status_code == 201
        # Confirm
        r3 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r3.status_code == 200, r3.content
        # Receivable created
        rec = Receivable.objects.first()
        assert rec is not None
        assert str(rec.amount) == "200.00"
        assert rec.method_id == pm.id

    def test_cannot_change_payment_after_confirm(self):
        pm = PaymentMethod.objects.create(code="pix", name="PIX", type="pix", auto_settle=True)
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id, "payment_method": pm.id},
            format="json",
        )
        order_id = r.json()["id"]
        # Add item and confirm
        self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {"product": self.product.id, "quantity": "1", "unit_price": "100.00"},
            format="json",
        )
        self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        # Try change payment method
        pm2 = PaymentMethod.objects.create(code="cash", name="Dinheiro", type="cash", auto_settle=True)
        r2 = self.client.patch(
            f"/api/v1/sale/orders/{order_id}/",
            {"payment_method": pm2.id},
            format="json",
        )
        assert r2.status_code == 400

    def test_confirm_auto_settles_immediate_method(self):
        pm = PaymentMethod.objects.create(code="pix", name="PIX", type="pix", settlement_days=0, auto_settle=True)
        # Create order
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id, "payment_method": pm.id},
            format="json",
        )
        order_id = r.json()["id"]
        # Add item
        self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {"product": self.product.id, "quantity": "1", "unit_price": "100.00"},
            format="json",
        )
        # Confirm
        r3 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r3.status_code == 200
        # Receivable should be paid
        rec = Receivable.objects.first()
        assert rec.status == "PAGO"
        assert str(rec.paid_amount) == str(rec.amount)

    def test_confirm_fails_if_insufficient_stock(self):
        # Create order with big qty
        r = self.client.post(
            "/api/v1/sale/orders/",
            {"seller": self.seller.id, "customer": self.customer.id},
            format="json",
        )
        order_id = r.json()["id"]
        r2 = self.client.post(
            f"/api/v1/sale/orders/{order_id}/add-item/",
            {"product": self.product.id, "quantity": "100", "unit_price": "200.00"},
            format="json",
        )
        assert r2.status_code == 201
        r3 = self.client.post(f"/api/v1/sale/orders/{order_id}/action/", {"action": "confirm"}, format="json")
        assert r3.status_code == 400
