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


class Strategy(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Section(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=60)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("strategy", "name")

    def __str__(self) -> str:
        return f"{self.strategy.name} - {self.name}"


class Step(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("section", "title")

    def __str__(self) -> str:
        return f"{self.section.name} - {self.title}"


class StepImage(models.Model):
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="step_images/")
    caption = models.CharField(max_length=180, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.step.title} image {self.id}"


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


class SessionRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_runs")
    strategy = models.ForeignKey(Strategy, on_delete=models.PROTECT, related_name="session_runs")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    symbol = models.CharField(max_length=20, blank=True, default="")
    day_notes = models.TextField(blank=True, default="")
    trade_taken = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.strategy.name} ({self.started_at:%Y-%m-%d})"


class StepCheck(models.Model):
    session_run = models.ForeignKey(SessionRun, on_delete=models.CASCADE, related_name="step_checks")
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name="checks")
    checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        unique_together = ("session_run", "step")
        ordering = ["step__section__order", "step__order", "id"]

    def __str__(self) -> str:
        return f"{self.session_run_id} - {self.step.title}"


class TradeDirection(models.TextChoices):
    LONG = "LONG", "Long"
    SHORT = "SHORT", "Short"


class Trade(models.Model):
    session_run = models.OneToOneField(SessionRun, on_delete=models.CASCADE, related_name="trade")
    direction = models.CharField(max_length=5, choices=TradeDirection.choices)
    entry_time = models.DateTimeField()
    stop = models.DecimalField(max_digits=12, decimal_places=4)
    target = models.DecimalField(max_digits=12, decimal_places=4)
    result_r = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-entry_time"]

    def __str__(self) -> str:
        return f"Trade {self.session_run_id} {self.direction} {self.result_r}R"
