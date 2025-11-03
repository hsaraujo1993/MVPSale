import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from purchase.models import PurchaseInvoice, PurchaseInstallment
from people.models import Supplier


User = get_user_model()


class InstallmentSummaryEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        today = datetime.date.today()
        self.sup1 = Supplier.objects.create(corporate_name="Forn 1", cnpj="11111111111111")
        self.sup2 = Supplier.objects.create(corporate_name="Forn 2", cnpj="22222222222222")
        inv1 = PurchaseInvoice.objects.create(number="10", series="1", supplier=self.sup1, total_value=0, xml="<xml/>")
        inv2 = PurchaseInvoice.objects.create(number="20", series="1", supplier=self.sup2, total_value=0, xml="<xml/>")
        PurchaseInstallment.objects.create(invoice=inv1, number="1", due_date=today - datetime.timedelta(days=1), value=100, status="ATRASADO")
        PurchaseInstallment.objects.create(invoice=inv1, number="2", due_date=today + datetime.timedelta(days=5), value=50, status="PENDENTE")
        PurchaseInstallment.objects.create(invoice=inv2, number="1", due_date=today + datetime.timedelta(days=10), value=70, status="PENDENTE")

    def test_summary_all_suppliers(self):
        r = self.client.get("/api/v1/purchase/installments/summary/")
        assert r.status_code == 200, r.content
        data = r.json()
        assert data["total"]["count"] == 3
        assert data["overdue"]["count"] == 1
        assert len(data["suppliers"]) == 2

    def test_summary_single_supplier(self):
        r = self.client.get(f"/api/v1/purchase/installments/summary/?supplier={self.sup1.id}")
        assert r.status_code == 200
        data = r.json()
        # Only sup1 installments: 2
        assert data["total"]["count"] == 2
        # Overdue for sup1: 1
        assert data["overdue"]["count"] == 1

