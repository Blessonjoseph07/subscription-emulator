import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from system_module.models import LifecycleEvent, Subscription, UsageLog

User = get_user_model()

class Command(BaseCommand):
    help = "Creates demo user and subscription data for testing"

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old demo data...")
        User.objects.filter(username="demo").delete()

        self.stdout.write("Creating demo user...")
        user = User.objects.create_user(username="demo", password="demo_password")

        today = timezone.localdate()

        self.stdout.write("Creating subscriptions...")
        subs_data = [
            {
                "name": "Netflix",
                "category": Subscription.Category.ENTERTAINMENT,
                "monthly_cost": Decimal("649.00"),
                "billing_day": 15,
                "started_on": today - timedelta(days=45),
                "status": Subscription.Status.ACTIVE,
            },
            {
                "name": "Spotify Premium",
                "category": Subscription.Category.ENTERTAINMENT,
                "monthly_cost": Decimal("119.00"),
                "billing_day": 5,
                "started_on": today - timedelta(days=90),
                "status": Subscription.Status.ACTIVE,
            },
            {
                "name": "Adobe Creative Cloud",
                "category": Subscription.Category.TOOLS,
                "monthly_cost": Decimal("2399.00"),
                "billing_day": 28,
                "started_on": today - timedelta(days=120),
                "status": Subscription.Status.ACTIVE,
            },
            {
                "name": "Cult.fit",
                "category": Subscription.Category.FITNESS,
                "monthly_cost": Decimal("1500.00"),
                "billing_day": 10,
                "started_on": today - timedelta(days=200),
                "status": Subscription.Status.PAUSED,
            },
        ]

        for data in subs_data:
            sub = Subscription.objects.create(user=user, **data)
            
            # Create activated event
            LifecycleEvent.objects.create(
                subscription=sub,
                event_type=LifecycleEvent.EventType.ACTIVATED,
                occurred_on=sub.started_on,
            )

            # Generate random usage logs for the current cycle
            start_date, end_date = sub.current_cycle(today)
            
            current_date = start_date
            while current_date <= today:
                # Decide if used today
                if data["status"] == Subscription.Status.ACTIVE:
                    # Netflix used often
                    if data["name"] == "Netflix" and random.random() < 0.7:
                        UsageLog.objects.create(subscription=sub, date=current_date, minutes_used=random.randint(45, 180))
                    # Spotify used very often
                    elif data["name"] == "Spotify Premium" and random.random() < 0.9:
                        UsageLog.objects.create(subscription=sub, date=current_date, minutes_used=random.randint(30, 240))
                    # Adobe used rarely
                    elif data["name"] == "Adobe Creative Cloud" and random.random() < 0.15:
                        UsageLog.objects.create(subscription=sub, date=current_date, minutes_used=random.randint(60, 300))
                
                current_date += timedelta(days=1)
                
            # If paused, add a paused event recently
            if data["status"] == Subscription.Status.PAUSED:
                pause_date = today - timedelta(days=7)
                LifecycleEvent.objects.create(
                    subscription=sub,
                    event_type=LifecycleEvent.EventType.PAUSED,
                    occurred_on=pause_date,
                    note="Taking a break",
                )

        self.stdout.write(self.style.SUCCESS("Successfully generated demo data!"))
        self.stdout.write(self.style.SUCCESS("You can now log in with username: 'demo' and password: 'demo_password'"))
