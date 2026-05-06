from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import LifecycleEvent, Subscription
from django.db.models import Sum

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def dashboard(request):
    events = LifecycleEvent.objects.all().select_related('subscription', 'subscription__user').order_by('-occurred_on', '-created_at')[:50]
    
    total_subs = Subscription.objects.count()
    active_subs = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
    paused_subs = Subscription.objects.filter(status=Subscription.Status.PAUSED).count()
    
    total_monthly_value = Subscription.objects.aggregate(Sum('monthly_cost'))['monthly_cost__sum'] or 0
    
    return render(request, 'system_module/dashboard.html', {
        'events': events,
        'total_subs': total_subs,
        'active_subs': active_subs,
        'paused_subs': paused_subs,
        'total_monthly_value': total_monthly_value,
    })
