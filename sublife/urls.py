from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from user_module import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="user_module/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("subscriptions/new/", views.create_subscription, name="create_subscription"),
    path("subscriptions/<int:pk>/", views.subscription_detail, name="subscription_detail"),
    path("subscriptions/<int:pk>/use/", views.log_usage, name="log_usage"),
    path("subscriptions/<int:pk>/pause/", views.pause_subscription, name="pause_subscription"),
    path("subscriptions/<int:pk>/resume/", views.resume_subscription, name="resume_subscription"),
    path("subscriptions/<int:pk>/renew/", views.renew_subscription, name="renew_subscription"),
    path("subscriptions/<int:pk>/cancel/", views.cancel_subscription, name="cancel_subscription"),
    path("admin-dashboard/", include("admin_module.urls")),
    path("system-dashboard/", include("system_module.urls")),
]
