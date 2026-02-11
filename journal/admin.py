from django.contrib import admin
from .models import Concept, DayJournal, JournalSlotItem

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
