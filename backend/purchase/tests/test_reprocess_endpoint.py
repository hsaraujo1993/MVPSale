import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from purchase.models import PurchaseInvoice, PurchaseInstallment
from people.models import Supplier


User = get_user_model()


class ReprocessEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        sup = Supplier.objects.create(corporate_name="Forn X", cnpj="12345678901234")
        inv = PurchaseInvoice.objects.create(number="1", series="1", supplier=sup, total_value=0, xml="<xml/>")
        today = datetime.date.today()
        PurchaseInstallment.objects.create(invoice=inv, number="1", due_date=today - datetime.timedelta(days=2), value=10)
        PurchaseInstallment.objects.create(invoice=inv, number="2", due_date=today + datetime.timedelta(days=2), value=10)

    def test_reprocess_marks_overdue(self):
        r = self.client.post("/api/v1/purchase/reprocess-installments/", {}, format="json")
        assert r.status_code == 200
        assert r.json()["updated"] == 1

