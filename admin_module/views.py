from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from system_module.models import Subscription
from django.contrib import messages

User = get_user_model()

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def dashboard(request):
    users = User.objects.all().order_by('-date_joined')
    subscriptions = Subscription.objects.all().select_related('user').order_by('-created_at')
    
    return render(request, 'admin_module/dashboard.html', {
        'users': users,
        'subscriptions': subscriptions,
    })

@user_passes_test(is_superuser)
def delete_user(request, pk):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, pk=pk)
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete yourself.")
        else:
            user_to_delete.delete()
            messages.success(request, f"User deleted successfully.")
    return redirect('admin_dashboard')

@user_passes_test(is_superuser)
def delete_subscription(request, pk):
    if request.method == 'POST':
        sub = get_object_or_404(Subscription, pk=pk)
        sub.delete()
        messages.success(request, "Subscription deleted successfully.")
    return redirect('admin_dashboard')
