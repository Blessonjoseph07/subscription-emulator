from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from system_module.models import Subscription, UsageLog


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ("name", "category", "monthly_cost", "billing_day", "started_on")
        widgets = {
            "started_on": forms.DateInput(attrs={"type": "date"}),
            "monthly_cost": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "billing_day": forms.NumberInput(attrs={"min": "1", "max": "31"}),
        }


class UsageLogForm(forms.ModelForm):
    class Meta:
        model = UsageLog
        fields = ("date", "minutes_used", "note")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "minutes_used": forms.NumberInput(attrs={"min": "0", "step": "5"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = timezone.localdate()
