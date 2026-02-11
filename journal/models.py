from django.conf import settings
from django.db import models
from django.utils import timezone

class Concept(models.Model):
    """
    ICT concept library item (BOS, CHoCH, FVG, iFVG, Liquidity Sweep, etc.)
    """
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Timeframe(models.TextChoices):
    DAILY = "D", "Daily"
    H4 = "4H", "4H"
    H1 = "1H", "1H"
    M15 = "15M", "15M"
    M5 = "5M", "5M"
    M1 = "1M", "1M (Optional)"


class DayJournal(models.Model):
    """
    One journal per user per calendar date.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    session = models.CharField(max_length=40, default="NY")
    symbol = models.CharField(max_length=20, blank=True, default="")

    trade_taken = models.BooleanField(default=False)
    why_taken = models.TextField(blank=True, default="")
    what_i_did_well = models.TextField(blank=True, default="")
    what_to_improve = models.TextField(blank=True, default="")
    general_notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.date}"


class JournalSlotItem(models.Model):
    """
    A concept placed into a timeframe slot for a given day journal.
    Ordered for drag/drop.
    """
    journal = models.ForeignKey(DayJournal, on_delete=models.CASCADE, related_name="slot_items")
    timeframe = models.CharField(max_length=10, choices=Timeframe.choices)
    concept = models.ForeignKey(Concept, on_delete=models.PROTECT)

    order = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        ordering = ["timeframe", "order"]

    def __str__(self) -> str:
        return f"{self.journal.date} {self.timeframe}: {self.concept.name}"
