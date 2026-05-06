from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

from django.utils import timezone

from system_module.models import LifecycleEvent, Subscription


MONEY = Decimal("0.01")


def quantize_money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def percent(part, whole):
    if not whole:
        return 0
    return max(0, min(100, round((part / whole) * 100)))


def heat_for_efficiency(efficiency):
    if efficiency >= 70:
        return {"label": "Efficient", "key": "green", "icon": "✓"}
    if efficiency >= 40:
        return {"label": "Moderate", "key": "yellow", "icon": "!"}
    return {"label": "High Waste", "key": "red", "icon": "!"}


def suspended_days_in_period(subscription, start, end):
    if end <= start:
        return 0

    state_events = (
        subscription.events.filter(
            event_type__in=[
                LifecycleEvent.EventType.PAUSED,
                LifecycleEvent.EventType.RESUMED,
                LifecycleEvent.EventType.CANCELLED,
            ],
            occurred_on__lt=end,
        )
        .order_by("occurred_on", "created_at", "id")
    )

    latest_before = None
    events_in_period = []
    for event in state_events:
        if event.occurred_on < start:
            latest_before = event
        else:
            events_in_period.append(event)

    suspended = bool(
        latest_before
        and latest_before.event_type
        in [LifecycleEvent.EventType.PAUSED, LifecycleEvent.EventType.CANCELLED]
    )
    suspended_start = start if suspended else None
    days = 0

    for event in events_in_period:
        if event.event_type in [
            LifecycleEvent.EventType.PAUSED,
            LifecycleEvent.EventType.CANCELLED,
        ]:
            if not suspended:
                suspended = True
                suspended_start = max(event.occurred_on, start)
        elif event.event_type == LifecycleEvent.EventType.RESUMED and suspended:
            days += max((min(event.occurred_on, end) - suspended_start).days, 0)
            suspended = False
            suspended_start = None

    if suspended and suspended_start:
        days += max((end - suspended_start).days, 0)

    return days


def subscription_snapshot(subscription, today=None):
    today = today or timezone.localdate()
    cycle_start, cycle_end = subscription.current_cycle(today)
    observed_end = min(cycle_end, today + timedelta(days=1))
    cycle_days = max((cycle_end - cycle_start).days, 1)
    observed_days = max((observed_end - cycle_start).days, 1)

    usage_dates = set(
        subscription.usage_logs.filter(
            date__gte=cycle_start,
            date__lt=observed_end,
        ).values_list("date", flat=True)
    )
    used_days = len(usage_dates)
    suspended_days = suspended_days_in_period(subscription, cycle_start, observed_end)
    billable_days = max(observed_days - suspended_days, 0)
    wasted_days = max(billable_days - used_days, 0)

    daily_rate = Decimal(subscription.monthly_cost) / Decimal(cycle_days)
    wasted_amount = quantize_money(daily_rate * Decimal(wasted_days))
    savings_from_pauses = quantize_money(daily_rate * Decimal(suspended_days))
    efficiency = percent(used_days, observed_days)
    heat = heat_for_efficiency(efficiency)
    days_until_billing = max((cycle_end - today).days, 0)

    active_pct = percent(used_days, observed_days)
    paused_pct = percent(suspended_days, observed_days)
    wasted_pct = max(0, 100 - active_pct - paused_pct)

    alert = None
    if subscription.status != Subscription.Status.CANCELLED and days_until_billing <= 3:
        if efficiency < 40:
            alert_level = "red"
            action = f"Pause before {cycle_end.strftime('%d %b')} to avoid more waste."
        elif efficiency < 70:
            alert_level = "yellow"
            action = "Review usage before renewal."
        else:
            alert_level = "green"
            action = "Renewing is currently worth it."

        alert = {
            "level": alert_level,
            "title": f"{subscription.name} bills in {days_until_billing} day{'s' if days_until_billing != 1 else ''}",
            "action": action,
        }

    return {
        "subscription": subscription,
        "cycle_start": cycle_start,
        "cycle_end": cycle_end,
        "cycle_days": cycle_days,
        "observed_days": observed_days,
        "used_days": used_days,
        "paused_days": suspended_days,
        "wasted_days": wasted_days,
        "billable_days": billable_days,
        "daily_rate": quantize_money(daily_rate),
        "wasted_amount": wasted_amount,
        "savings_from_pauses": savings_from_pauses,
        "efficiency": efficiency,
        "heat": heat,
        "days_until_billing": days_until_billing,
        "segments": {
            "active": active_pct,
            "paused": paused_pct,
            "wasted": wasted_pct,
        },
        "alert": alert,
    }


def portfolio_summary(snapshots):
    total_subs = len(snapshots)
    total_spent = sum(
        (Decimal(item["subscription"].monthly_cost) for item in snapshots),
        Decimal("0.00"),
    )
    total_wasted = sum((item["wasted_amount"] for item in snapshots), Decimal("0.00"))
    avg_efficiency = (
        round(sum(item["efficiency"] for item in snapshots) / total_subs)
        if total_subs
        else 0
    )
    waste_rate = percent(float(total_wasted), float(total_spent)) if total_spent else 0

    return {
        "total_subs": total_subs,
        "total_spent": quantize_money(total_spent),
        "total_wasted": quantize_money(total_wasted),
        "waste_rate": waste_rate,
        "efficiency": avg_efficiency,
        "alerts": [item["alert"] for item in snapshots if item["alert"]],
    }


def category_breakdown(snapshots):
    totals = {}
    for item in snapshots:
        subscription = item["subscription"]
        label = subscription.get_category_display()
        totals[label] = totals.get(label, Decimal("0.00")) + Decimal(subscription.monthly_cost)

    overall = sum(totals.values(), Decimal("0.00")) or Decimal("1.00")
    return [
        {
            "name": name,
            "amount": quantize_money(amount),
            "percent": percent(float(amount), float(overall)),
        }
        for name, amount in sorted(totals.items())
    ]


def get_smart_suggestions(snapshots):
    suggestions = []
    for item in snapshots:
        sub = item["subscription"]
        if sub.status != Subscription.Status.ACTIVE:
            continue
            
        if item["wasted_amount"] > 0 and item["efficiency"] < 50:
            suggestions.append({
                "type": "cancel",
                "title": f"Waste Detected: {sub.name}",
                "text": f"You have already wasted ₹{item['wasted_amount']} on {sub.name} this cycle. Consider pausing it to stop the bleed."
            })
        elif item["used_days"] == 0 and item["observed_days"] >= 14:
            suggestions.append({
                "type": "warning",
                "title": f"Unused: {sub.name}",
                "text": f"You haven't tracked any usage for {sub.name} in over {item['observed_days']} days. Consider pausing it to save ₹{sub.monthly_cost} next cycle."
            })
        elif item["efficiency"] < 35 and item["days_until_billing"] <= 7:
            suggestions.append({
                "type": "warning",
                "title": f"Low Value: {sub.name}",
                "text": f"{sub.name} renews in {item['days_until_billing']} days, but your efficiency is only {item['efficiency']}%. Pause it before it bills."
            })
            
    if not suggestions:
        suggestions.append({
            "type": "positive",
            "title": "Looking Good!",
            "text": "Your subscriptions are highly utilized right now. No obvious waste detected!"
        })
        
    return suggestions
