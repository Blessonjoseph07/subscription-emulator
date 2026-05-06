from django.contrib import admin

from system_module.models import LifecycleEvent, Subscription, UsageLog


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "monthly_cost", "billing_day", "status")
    list_filter = ("category", "status")
    search_fields = ("name", "user__username")


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ("subscription", "date", "minutes_used")
    list_filter = ("date",)
    search_fields = ("subscription__name",)


@admin.register(LifecycleEvent)
class LifecycleEventAdmin(admin.ModelAdmin):
    list_display = ("subscription", "event_type", "occurred_on")
    list_filter = ("event_type", "occurred_on")
    search_fields = ("subscription__name",)
