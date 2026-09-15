from django.contrib.auth import views as auth_views
from django.urls import path

from . import api, health, integrations, views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('healthz/', health.healthz, name='healthz'),
    path('cadastro/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=__import__('extractor.forms', fromlist=['RateLimitedAuthenticationForm']).RateLimitedAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('historico/apagar/', views.clear_history, name='clear_history'),
    path('api/v1/token/', api.token, name='api-token'),
    path('api/v1/token/revoke/', api.revoke_token, name='api-token-revoke'),
    path('api/v1/integrations/', integrations.integrations, name='api-integrations'),
    path('api/v1/integrations/<int:pk>/', integrations.integration_detail, name='api-integration-detail'),
    path('api/v1/prescriptions/', api.prescriptions, name='api-prescriptions'),
    path('api/v1/prescriptions/<int:pk>/', api.prescription_detail, name='api-prescription-detail'),
]
