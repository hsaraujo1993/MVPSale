from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient


class CepLookupTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Auth not strictly required for this test since viewset is protected by default.
        # Obtain token
        from django.contrib.auth.models import User

        user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @override_settings(WEBMANIA_APP_KEY="key", WEBMANIA_APP_SECRET="secret", WEBMANIA_CEP_ENABLED=True)
    @patch("people.services.cep.requests.get")
    def test_customer_creation_fills_address_from_webmania(self, mock_get):
        # First call: Webmania returns data
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "cep": "01001-000",
            "endereco": "Praça da Sé",
            "bairro": "Sé",
            "cidade": "São Paulo",
            "uf": "SP",
        }

        payload = {
            "name": "Maria",
            "cpf_cnpj": "12345678901",
            "cep": "01001000",
            "email": "maria@example.com",
            # address/city/uf omitted to be filled by service
        }
        r = self.client.post("/api/v1/people/customers/", payload, format="json")
        assert r.status_code == 201, r.content
        data = r.json()
        assert data["address"].startswith("Praça da Sé")
        assert data["city"] == "São Paulo"
        assert data["uf"] == "SP"

