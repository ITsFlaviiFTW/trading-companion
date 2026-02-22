from django.apps import apps
from django.contrib import admin, messages
from django.db import transaction
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
    actions = ["clone_selected_strategies"]

    @admin.action(description="Clone selected strategies (deep copy)")
    def clone_selected_strategies(self, request, queryset):
        cloned_count = 0

        sections_accessor = self._related_accessor(Strategy, Section, "strategy")
        steps_accessor = self._related_accessor(Section, Step, "section")

        step_image_model = self._get_step_image_model()
        images_accessor = None
        if step_image_model is not None:
            images_accessor = self._related_accessor(Step, step_image_model, "step")

        for strategy in queryset.order_by("id"):
            with transaction.atomic():
                cloned_strategy = Strategy.objects.create(
                    name=self._next_copy_name(strategy.name),
                    description=strategy.description,
                    is_active=strategy.is_active,
                )

                original_sections = getattr(strategy, sections_accessor).all().order_by("order", "id")
                for original_section in original_sections:
                    cloned_section = Section.objects.create(
                        strategy=cloned_strategy,
                        name=original_section.name,
                        order=original_section.order,
                    )

                    original_steps = getattr(original_section, steps_accessor).all().order_by("order", "id")
                    for original_step in original_steps:
                        cloned_step = Step.objects.create(
                            section=cloned_section,
                            order=original_step.order,
                            title=original_step.title,
                            description=original_step.description,
                            required=original_step.required,
                        )

                        if step_image_model is None or not images_accessor:
                            continue

                        original_images = getattr(original_step, images_accessor).all().order_by("order", "id")
                        for original_image in original_images:
                            payload = {"step": cloned_step}
                            for field in step_image_model._meta.get_fields():
                                if not getattr(field, "concrete", False) or getattr(field, "many_to_many", False):
                                    continue
                                if field.auto_created or field.primary_key or field.name == "step":
                                    continue
                                payload[field.name] = getattr(original_image, field.name)
                            step_image_model.objects.create(**payload)

                cloned_count += 1

        self.message_user(request, f"Cloned {cloned_count} strategies.", level=messages.SUCCESS)

    def _related_accessor(self, parent_model, child_model, fk_name):
        for rel in parent_model._meta.related_objects:
            if rel.related_model is child_model and rel.field.name == fk_name:
                return rel.get_accessor_name()
        raise ValueError(f"Could not resolve relation {parent_model.__name__} -> {child_model.__name__}")

    def _next_copy_name(self, original_name):
        base = f"{original_name} (Copy)"
        if not Strategy.objects.filter(name=base).exists():
            return base

        index = 2
        while True:
            candidate = f"{original_name} (Copy {index})"
            if not Strategy.objects.filter(name=candidate).exists():
                return candidate
            index += 1

    def _get_step_image_model(self):
        try:
            return apps.get_model("journal", "StepImage")
        except LookupError:
            return None


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
