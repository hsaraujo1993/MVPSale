from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from people.views import CustomerViewSet


urlpatterns = [
    path("admin/", admin.site.urls),

    # Legacy/public CEP endpoints
    path("api/people/cep/", CustomerViewSet.as_view({"get": "cep_lookup"})),
    path("api/cep/", CustomerViewSet.as_view({"get": "cep_lookup"})),

    # API routes
    path("api/v1/", include("api.urls")),
    path("api/", include("api.urls")),

    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Pages
    path("", login_required(TemplateView.as_view(template_name="dashboard.html")), name="home"),
    path("login", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html")),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/")),

    # Public pages used by E2E (rely on JWT localStorage when needed)
    path("home", TemplateView.as_view(template_name="home.html"), name="home"),
    path("home/", TemplateView.as_view(template_name="home.html")),
    path("catalog", TemplateView.as_view(template_name="catalog.html"), name="catalog"),
    path("price-review", TemplateView.as_view(template_name="catalog/price_review.html"), name="price-review"),
    path("nfe", TemplateView.as_view(template_name="nfe.html"), name="nfe"),
    path("sales", login_required(TemplateView.as_view(template_name="sales.html")), name="sales"),

    # Other gated pages
    path("cashier", login_required(TemplateView.as_view(template_name="cashier.html")), name="cashier"),
    path("orders", login_required(TemplateView.as_view(template_name="orders.html")), name="orders"),
    path("orders/confirm", login_required(TemplateView.as_view(template_name="orders/confirm.html")), name="orders-confirm"),
    path("payments", login_required(TemplateView.as_view(template_name="payments.html")), name="payments"),
    path("people", login_required(TemplateView.as_view(template_name="people.html")), name="people"),
    path("purchase", login_required(TemplateView.as_view(template_name="purchase.html")), name="purchase"),
    path("stock", login_required(TemplateView.as_view(template_name="stock.html")), name="stock"),
    path("integrations", login_required(TemplateView.as_view(template_name="integrations.html")), name="integrations"),
    path("settings", login_required(TemplateView.as_view(template_name="settings.html")), name="settings"),
]

# Auth (SimpleJWT + password change)
urlpatterns += [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Aliases expected by Novo Front login
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair_alias"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_alias"),
    path(
        "password_change/",
        login_required(auth_views.PasswordChangeView.as_view(template_name="auth/password_change_form.html")),
        name="password_change",
    ),
    path(
        "password_change/done/",
        login_required(auth_views.PasswordChangeDoneView.as_view(template_name="auth/password_change_done.html")),
        name="password_change_done",
    ),
]

