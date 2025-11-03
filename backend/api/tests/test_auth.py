from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class AuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "tester"
        self.password = "pass1234"
        User.objects.create_user(username=self.username, password=self.password)

    def test_obtain_and_refresh(self):
        resp = self.client.post("/api/token/", {"username": self.username, "password": self.password}, format="json")
        assert resp.status_code == 200, resp.content
        access = resp.json().get("access")
        refresh = resp.json().get("refresh")
        assert access and refresh

        resp2 = self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json")
        assert resp2.status_code == 200
        assert resp2.json().get("access")

