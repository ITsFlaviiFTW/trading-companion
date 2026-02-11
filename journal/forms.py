from django import forms
from .models import DayJournal

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
