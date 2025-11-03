from django.test import TestCase
from rest_framework.test import APIClient


class HealthTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_ok(self):
        resp = self.client.get("/api/v1/health/")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

