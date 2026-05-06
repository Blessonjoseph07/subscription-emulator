from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('user/<int:pk>/delete/', views.delete_user, name='admin_delete_user'),
    path('subscription/<int:pk>/delete/', views.delete_subscription, name='admin_delete_subscription'),
]
