from django.test import TestCase
from rest_framework.test import APIClient


class SchemaTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_schema_and_uis(self):
        resp = self.client.get("/api/schema/")
        assert resp.status_code == 200

        resp_swagger = self.client.get("/api/schema/swagger/")
        assert resp_swagger.status_code == 200

        resp_redoc = self.client.get("/api/schema/redoc/")
        assert resp_redoc.status_code == 200

