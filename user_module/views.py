from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from user_module.forms import SignupForm, SubscriptionForm, UsageLogForm
from system_module.metrics import category_breakdown, portfolio_summary, subscription_snapshot, get_smart_suggestions
from system_module.models import LifecycleEvent, Subscription, UsageLog


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to SubLife. Add your first subscription.")
            return redirect("dashboard")
    else:
        form = SignupForm()

    return render(request, "user_module/signup.html", {"form": form})


@login_required
def dashboard(request):
    subscriptions = (
        request.user.subscriptions.all()
        .prefetch_related("usage_logs", "events")
        .order_by("name")
    )
    snapshots = [subscription_snapshot(subscription) for subscription in subscriptions]
    summary = portfolio_summary(snapshots)
    categories = category_breakdown(snapshots)
    simulator_source = snapshots[0] if snapshots else None
    suggestions = get_smart_suggestions(snapshots)

    return render(
        request,
        "user_module/dashboard.html",
        {
            "subscription_form": SubscriptionForm(),
            "usage_form": UsageLogForm(),
            "snapshots": snapshots,
            "summary": summary,
            "categories": categories,
            "simulator_source": simulator_source,
            "suggestions": suggestions,
            "today": timezone.localdate(),
        },
    )


@login_required
@transaction.atomic
def create_subscription(request):
    if request.method != "POST":
        return redirect("dashboard")

    form = SubscriptionForm(request.POST)
    if form.is_valid():
        subscription = form.save(commit=False)
        subscription.user = request.user
        subscription.save()
        LifecycleEvent.objects.create(
            subscription=subscription,
            event_type=LifecycleEvent.EventType.ACTIVATED,
            occurred_on=subscription.started_on,
            note="Subscription added to SubLife.",
        )
        messages.success(request, f"{subscription.name} is now being tracked.")
    else:
        messages.error(request, "Could not add subscription. Check the values and try again.")

    return redirect("dashboard")


@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    return render(
        request,
        "user_module/subscription_detail.html",
        {
            "subscription": subscription,
            "snapshot": subscription_snapshot(subscription),
            "usage_form": UsageLogForm(),
            "usage_logs": subscription.usage_logs.all()[:20],
            "events": subscription.events.all()[:20],
        },
    )


@login_required
def log_usage(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method != "POST":
        return redirect("subscription_detail", pk=subscription.pk)

    if subscription.status == Subscription.Status.CANCELLED:
        messages.error(request, "Cancelled subscriptions cannot receive new usage logs.")
        return redirect("subscription_detail", pk=subscription.pk)

    form = UsageLogForm(request.POST)
    if form.is_valid():
        usage, created = UsageLog.objects.update_or_create(
            subscription=subscription,
            date=form.cleaned_data["date"],
            defaults={
                "minutes_used": form.cleaned_data["minutes_used"] or 0,
                "note": form.cleaned_data["note"],
            },
        )
        verb = "Logged" if created else "Updated"
        messages.success(request, f"{verb} usage for {subscription.name} on {usage.date}.")
    else:
        messages.error(request, "Could not log usage. Check the date and minutes.")

    return redirect("subscription_detail", pk=subscription.pk)


@login_required
@transaction.atomic
def pause_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST" and subscription.status == Subscription.Status.ACTIVE:
        subscription.status = Subscription.Status.PAUSED
        subscription.save(update_fields=["status", "updated_at"])
        LifecycleEvent.objects.create(
            subscription=subscription,
            event_type=LifecycleEvent.EventType.PAUSED,
            note="Paused from dashboard.",
        )
        messages.success(request, f"{subscription.name} is paused.")
    return redirect(request.POST.get("next") or "dashboard")


@login_required
@transaction.atomic
def resume_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST" and subscription.status == Subscription.Status.PAUSED:
        subscription.status = Subscription.Status.ACTIVE
        subscription.save(update_fields=["status", "updated_at"])
        LifecycleEvent.objects.create(
            subscription=subscription,
            event_type=LifecycleEvent.EventType.RESUMED,
            note="Resumed from dashboard.",
        )
        messages.success(request, f"{subscription.name} is active again.")
    return redirect(request.POST.get("next") or "dashboard")


@login_required
@transaction.atomic
def renew_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST":
        subscription.status = Subscription.Status.ACTIVE
        subscription.save(update_fields=["status", "updated_at"])
        LifecycleEvent.objects.create(
            subscription=subscription,
            event_type=LifecycleEvent.EventType.RENEWED,
            note="Renewal confirmed.",
        )
        messages.success(request, f"{subscription.name} renewal was recorded.")
    return redirect(request.POST.get("next") or "dashboard")


@login_required
@transaction.atomic
def cancel_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk, user=request.user)
    if request.method == "POST" and subscription.status != Subscription.Status.CANCELLED:
        subscription.status = Subscription.Status.CANCELLED
        subscription.save(update_fields=["status", "updated_at"])
        LifecycleEvent.objects.create(
            subscription=subscription,
            event_type=LifecycleEvent.EventType.CANCELLED,
            note="Cancelled from dashboard.",
        )
        messages.success(request, f"{subscription.name} is cancelled.")
    return redirect(request.POST.get("next") or "dashboard")
