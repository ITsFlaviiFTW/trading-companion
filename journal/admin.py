from django.contrib import admin
from .models import (
    Concept,
    DayJournal,
    JournalSlotItem,
    Section,
    SessionRun,
    Step,
    StepCheck,
    StepImage,
    Strategy,
    Trade,
)

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)

class JournalSlotItemInline(admin.TabularInline):
    model = JournalSlotItem
    extra = 0

@admin.register(DayJournal)
class DayJournalAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "session", "symbol", "trade_taken", "updated_at")
    list_filter = ("session", "trade_taken", "date")
    search_fields = ("user__username", "symbol")
    inlines = [JournalSlotItemInline]


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ("name", "order")
    ordering = ("order", "id")


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "strategy", "order")
    list_filter = ("strategy",)
    search_fields = ("name", "strategy__name")
    ordering = ("strategy", "order", "id")


class StepImageInline(admin.TabularInline):
    model = StepImage
    extra = 1
    fields = ("image", "caption", "order")
    ordering = ("order", "id")


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "order", "required")
    list_filter = ("section__strategy", "section", "required")
    search_fields = ("title", "section__name", "section__strategy__name")
    ordering = ("section", "order", "id")
    inlines = [StepImageInline]


@admin.register(SessionRun)
class SessionRunAdmin(admin.ModelAdmin):
    list_display = ("user", "strategy", "symbol", "started_at", "completed", "trade_taken")
    list_filter = ("completed", "trade_taken", "strategy")
    search_fields = ("user__username", "symbol", "strategy__name")
    ordering = ("-started_at",)


@admin.register(StepCheck)
class StepCheckAdmin(admin.ModelAdmin):
    list_display = ("session_run", "step", "checked", "checked_at")
    list_filter = ("checked", "step__section__strategy")
    search_fields = ("session_run__user__username", "step__title")


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("session_run", "direction", "entry_time", "result_r")
    list_filter = ("direction",)
    search_fields = ("session_run__user__username", "session_run__symbol", "notes")
