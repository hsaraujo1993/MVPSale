from django.contrib import admin
from django.urls import path, include
from people.views import CustomerViewSet
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),
    # Backwards-compatible CEP endpoint used by legacy frontend calls
    path("api/people/cep/", CustomerViewSet.as_view({"get": "cep_lookup"})),
    # Public, short CEP endpoint
    path("api/cep/", CustomerViewSet.as_view({"get": "cep_lookup"})),
    # API routes (v1 and non-versioned alias for frontend)
    path("api/v1/", include("api.urls")),
    path("api/", include("api.urls")),

    # OpenAPI schema and UIs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Novo Front pages (gated)
    path("", login_required(TemplateView.as_view(template_name="dashboard.html")), name="home"),
    path("login", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html")),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/")),
    path("home", login_required(TemplateView.as_view(template_name="home.html")), name="home"),
    path("home/", login_required(TemplateView.as_view(template_name="home.html"))),
    path("catalog", login_required(TemplateView.as_view(template_name="catalog.html")), name="catalog"),
    path("cashier", login_required(TemplateView.as_view(template_name="cashier.html")), name="cashier"),
    path("orders", login_required(TemplateView.as_view(template_name="orders.html")), name="orders"),
    path("payments", login_required(TemplateView.as_view(template_name="payments.html")), name="payments"),
    path("people", login_required(TemplateView.as_view(template_name="people.html")), name="people"),
    path("purchase", login_required(TemplateView.as_view(template_name="purchase.html")), name="purchase"),
    path("stock", login_required(TemplateView.as_view(template_name="stock.html")), name="stock"),
    path("nfe", login_required(TemplateView.as_view(template_name="nfe.html")), name="nfe"),
    path("integrations", login_required(TemplateView.as_view(template_name="integrations.html")), name="integrations"),
    path("settings", login_required(TemplateView.as_view(template_name="settings.html")), name="settings"),
    path("sales", login_required(TemplateView.as_view(template_name="sales.html")), name="sales"),
]

# Auth (SimpleJWT)
urlpatterns += [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Aliases expected by Novo Front login
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair_alias"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_alias"),
    # Password change (session auth)
    path("password_change/", login_required(auth_views.PasswordChangeView.as_view(template_name="auth/password_change_form.html")), name="password_change"),
    path("password_change/done/", login_required(auth_views.PasswordChangeDoneView.as_view(template_name="auth/password_change_done.html")), name="password_change_done"),
]
