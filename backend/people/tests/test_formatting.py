from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class FormattingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_customer_formats_cep_and_phone(self):
        payload = {
            "name": "Jose",
            "cpf_cnpj": "12345678901",
            "cep": "01001000",
            "phone": "11987654321",
        }
        r = self.client.post("/api/v1/people/customers/", payload, format="json")
        assert r.status_code == 201, r.content
        data = r.json()
        assert data["cep"] == "01001-000"
        assert data["phone"].startswith("(11) 98765-4321")

