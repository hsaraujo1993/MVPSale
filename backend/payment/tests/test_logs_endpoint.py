import os
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class PaymentLogsEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_logs_endpoint_returns_tail(self):
        log_dir = os.path.join(settings.BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "payment.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("test line 1\n")
            f.write("test line 2\n")
        r = self.client.get("/api/v1/payment/logs/")
        assert r.status_code == 200, r.content
        data = r.json()
        assert data["count"] >= 2
        assert any("test line" in ln for ln in data["lines"]) 

