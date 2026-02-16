from django import forms
from django.utils import timezone

from .models import DayJournal, SessionRun, Strategy, Trade

class DayJournalForm(forms.ModelForm):
    class Meta:
        model = DayJournal
        fields = [
            "session",
            "symbol",
            "trade_taken",
            "why_taken",
            "what_i_did_well",
            "what_to_improve",
            "general_notes",
        ]
        widgets = {
            "why_taken": forms.Textarea(attrs={"rows": 3}),
            "what_i_did_well": forms.Textarea(attrs={"rows": 3}),
            "what_to_improve": forms.Textarea(attrs={"rows": 3}),
            "general_notes": forms.Textarea(attrs={"rows": 3}),
        }


class StartSessionRunForm(forms.ModelForm):
    strategy = forms.ModelChoiceField(
        queryset=Strategy.objects.filter(is_active=True).order_by("name"),
        empty_label=None,
    )

    class Meta:
        model = SessionRun
        fields = ["strategy", "symbol"]
        widgets = {
            "symbol": forms.TextInput(attrs={"placeholder": "MNQ, SI, NQ, ES...", "autofocus": True}),
        }


class SessionRunReviewForm(forms.ModelForm):
    class Meta:
        model = SessionRun
        fields = ["trade_taken", "day_notes"]
        widgets = {
            "day_notes": forms.Textarea(attrs={"rows": 4}),
        }


class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = ["direction", "entry_time", "stop", "target", "result_r", "notes"]
        widgets = {
            "entry_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial["entry_time"] = timezone.localtime().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
