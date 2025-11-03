from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthView
from catalog.views import CategoryViewSet, BrandViewSet, ProductViewSet, PromotionViewSet
from people.views import CustomerViewSet, SupplierViewSet, SellerViewSet
from people.views import UserViewSet
from stock.views import StockViewSet, StockMovementViewSet
from purchase.views import (
    NFeImportView,
    ReprocessInstallmentsView,
    InstallmentSummaryView,
    PurchaseInvoiceViewSet,
)
from sale.views import OrderViewSet
from payment.views import (
    PaymentMethodViewSet,
    ReceivableViewSet,
    PaymentLogsView,
    CardBrandViewSet,
    CardFeeTierViewSet,
)
from nfe.views import NFeInvoiceViewSet, CompanyViewSet
from cashier.views import CashierSessionViewSet, CashMovementViewSet


urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]

# Catalog routes
router = DefaultRouter()
router.register(r"catalog/categories", CategoryViewSet, basename="category")
router.register(r"catalog/brands", BrandViewSet, basename="brand")
router.register(r"catalog/products", ProductViewSet, basename="product")
router.register(r"catalog/promotions", PromotionViewSet, basename="promotion")
router.register(r"people/customers", CustomerViewSet, basename="customer")
router.register(r"people/suppliers", SupplierViewSet, basename="supplier")
router.register(r"people/sellers", SellerViewSet, basename="seller")
router.register(r"people/users", UserViewSet, basename="user")
router.register(r"stock/movements", StockMovementViewSet, basename="stock-movement")
router.register(r"stock", StockViewSet, basename="stock")
router.register(r"sale/orders", OrderViewSet, basename="sale-order")
router.register(r"payment/methods", PaymentMethodViewSet, basename="payment-method")
router.register(r"payment/receivables", ReceivableViewSet, basename="payment-receivable")
router.register(r"payment/card-brands", CardBrandViewSet, basename="payment-card-brand")
router.register(r"payment/card-fees", CardFeeTierViewSet, basename="payment-card-fee")
router.register(r"payment/logs", PaymentLogsView, basename="payment-logs")
router.register(r"nfe/invoices", NFeInvoiceViewSet, basename="nfe-invoice")
router.register(r"nfe/companies", CompanyViewSet, basename="nfe-company")
router.register(r"cashier/sessions", CashierSessionViewSet, basename="cashier-session")
router.register(r"cashier/movements", CashMovementViewSet, basename="cashier-movement")
router.register(r"purchase/invoices", PurchaseInvoiceViewSet, basename="purchase-invoice")

urlpatterns += [
    # Compatibility route: some frontend code may call /api/people/cep/ directly.
    # Forward GET requests to the CustomerViewSet.cep_lookup action.
    path("people/cep/", CustomerViewSet.as_view({"get": "cep_lookup"}), name="people-cep-compat"),
    path("", include(router.urls)),
    path("purchase/import-xml/", NFeImportView.as_view(), name="purchase-import-xml"),
    path("purchase/reprocess-installments/", ReprocessInstallmentsView.as_view(), name="purchase-reprocess-installments"),
    path("purchase/installments/summary/", InstallmentSummaryView.as_view(), name="purchase-installments-summary"),
]
