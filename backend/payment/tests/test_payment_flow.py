import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from payment.models import PaymentMethod, Receivable


User = get_user_model()


class PaymentFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_method_receivable_settle_and_summary(self):
        # Create method
        r = self.client.post(
            "/api/v1/payment/methods/",
            {"code": "pix", "name": "PIX", "type": "pix", "fee_percent": "0.000", "fee_fixed": "0.00", "settlement_days": 0},
            format="json",
        )
        assert r.status_code == 201, r.content
        method_id = r.json()["id"]

        # Create receivable
        today = datetime.date.today().isoformat()
        r2 = self.client.post(
            "/api/v1/payment/receivables/",
            {"method": method_id, "amount": "100.00", "due_date": today, "reference": "order-1"},
            format="json",
        )
        assert r2.status_code == 201, r2.content
        rec_id = r2.json()["id"]

        # Settle receivable
        r3 = self.client.post(
            f"/api/v1/payment/receivables/{rec_id}/settle/",
            {"amount": "100.00", "paid_date": today, "external_id": "evt-1"},
            format="json",
        )
        assert r3.status_code == 200, r3.content
        assert r3.json()["status"] == "PAGO"

        # Summary
        r4 = self.client.get("/api/v1/payment/receivables/summary/")
        assert r4.status_code == 200

