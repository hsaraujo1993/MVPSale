from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from catalog.models import Product
from people.models import Supplier
from stock.models import Stock


User = get_user_model()


MIN_XML = """
<nfeProc>
  <NFe>
    <infNFe>
      <ide>
        <nNF>123</nNF>
        <serie>1</serie>
        <dhEmi>2025-01-15T12:00:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>Fornecedor ABC</xNome>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>ABC001</cProd>
          <xProd>Produto Teste</xProd>
          <NCM>12345678</NCM>
          <CFOP>5102</CFOP>
          <CEST>1234567</CEST>
          <cEAN>7891234567890</cEAN>
          <uCom>UN</uCom>
          <qCom>2.000</qCom>
          <vUnCom>10.00</vUnCom>
          <uTrib>UN</uTrib>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <orig>0</orig>
              <CST>00</CST>
            </ICMS00>
          </ICMS>
          <PIS>
            <PISAliq>
              <CST>01</CST>
              <pPIS>1.65</pPIS>
            </PISAliq>
          </PIS>
          <COFINS>
            <COFINSAliq>
              <CST>01</CST>
              <pCOFINS>7.60</pCOFINS>
            </COFINSAliq>
          </COFINS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vNF>20.00</vNF>
        </ICMSTot>
      </total>
      <cobr>
        <dup>
          <nDup>1</nDup>
          <dVenc>2025-02-15</dVenc>
          <vDup>20.00</vDup>
        </dup>
      </cobr>
    </infNFe>
  </NFe>
</nfeProc>
"""


class PurchaseImportTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        token = self.client.post("/api/token/", {"username": "tester", "password": "pass1234"}, format="json").json()[
            "access"
        ]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_import_xml_creates_entities_and_stock(self):
        r = self.client.post("/api/v1/purchase/import-xml/", {"xml_text": MIN_XML}, format="json")
        assert r.status_code == 201, r.content
        # Supplier created
        assert Supplier.objects.count() == 1
        # Product created
        p = Product.objects.first()
        assert p is not None and p.stock.quantity_current == 2
        # Stock status computed
        assert p.stock.status in ("ZERADO", "ABAIXO", "OK", "ACIMA")

