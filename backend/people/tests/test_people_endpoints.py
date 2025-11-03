from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class PeopleApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_customer_supplier_create_and_validation(self):
        # Customer with invalid cpf_cnpj -> 400
        r = self.client.post(
            "/api/v1/people/customers/",
            {"name": "Joao", "cpf_cnpj": "123"},
            format="json",
        )
        assert r.status_code == 400 and "cpf_cnpj" in r.json()

        # Valid customer
        r = self.client.post(
            "/api/v1/people/customers/",
            {"name": "Joao", "cpf_cnpj": "12345678901", "email": "j@a.com"},
            format="json",
        )
        assert r.status_code == 201

        # Supplier invalid cnpj -> 400
        r = self.client.post(
            "/api/v1/people/suppliers/",
            {"corporate_name": "Fornecedora X", "cnpj": "111"},
            format="json",
        )
        assert r.status_code == 400 and "cnpj" in r.json()

        # Supplier valid
        r = self.client.post(
            "/api/v1/people/suppliers/",
            {"corporate_name": "Fornecedora X", "cnpj": "12345678901234"},
            format="json",
        )
        assert r.status_code == 201

    def test_seller_create_and_group_membership(self):
        other = User.objects.create_user(username="selleruser", password="pass1234")
        r = self.client.post(
            "/api/v1/people/sellers/",
            {"user": other.id, "name": "Vendedor", "access_level": "desconto", "discount_max": "10.00"},
            format="json",
        )
        assert r.status_code == 201, r.content
        # Discount bounds
        r2 = self.client.post(
            "/api/v1/people/sellers/",
            {"user": self.user.id, "name": "Vendedor2", "access_level": "desconto", "discount_max": "200.00"},
            format="json",
        )
        assert r2.status_code == 400 and "discount_max" in r2.json()

