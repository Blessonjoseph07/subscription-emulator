import calendar
from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    class Category(models.TextChoices):
        ENTERTAINMENT = "entertainment", "Entertainment"
        FITNESS = "fitness", "Fitness"
        LEARNING = "learning", "Learning"
        TOOLS = "tools", "Tools"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.ENTERTAINMENT,
    )
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2)
    billing_day = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of the month the subscription renews.",
    )
    started_on = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @staticmethod
    def billing_date_for(year, month, billing_day):
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(billing_day, last_day))

    @staticmethod
    def shifted_month(year, month, offset):
        month_index = month - 1 + offset
        return year + month_index // 12, month_index % 12 + 1

    def current_cycle(self, today=None):
        today = today or timezone.localdate()
        this_month_bill = self.billing_date_for(today.year, today.month, self.billing_day)

        if today >= this_month_bill:
            start = this_month_bill
            end_year, end_month = self.shifted_month(today.year, today.month, 1)
            end = self.billing_date_for(end_year, end_month, self.billing_day)
        else:
            start_year, start_month = self.shifted_month(today.year, today.month, -1)
            start = self.billing_date_for(start_year, start_month, self.billing_day)
            end = this_month_bill

        return max(start, self.started_on), end

    def next_billing_date(self, today=None):
        return self.current_cycle(today)[1]


class UsageLog(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="usage_logs",
    )
    date = models.DateField(default=timezone.localdate)
    minutes_used = models.PositiveIntegerField(default=0, blank=True)
    note = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["subscription", "date"],
                name="unique_usage_per_subscription_day",
            )
        ]

    def __str__(self):
        return f"{self.subscription} used on {self.date}"


class LifecycleEvent(models.Model):
    class EventType(models.TextChoices):
        ACTIVATED = "activated", "Activated"
        PAUSED = "paused", "Paused"
        RESUMED = "resumed", "Resumed"
        RENEWED = "renewed", "Renewed"
        CANCELLED = "cancelled", "Cancelled"

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=24, choices=EventType.choices)
    occurred_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_on", "-created_at"]

    def __str__(self):
        return f"{self.subscription} {self.get_event_type_display()} on {self.occurred_on}"
