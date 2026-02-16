import calendar
import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import DayJournalForm, SessionRunReviewForm, StartSessionRunForm, TradeForm
from .models import (
    Concept,
    DayJournal,
    JournalSlotItem,
    Section,
    SessionRun,
    Step,
    StepCheck,
    Strategy,
    Timeframe,
    Trade,
)

def _get_or_create_journal(user, dt: date) -> DayJournal:
    journal, _ = DayJournal.objects.get_or_create(user=user, date=dt)
    return journal


def service_worker_view(request):
    js = """
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("tc-v1").then(cache => cache.addAll([
      "/",
      "/runs/start/",
      "/strategies/"
    ]))
  );
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
"""
    return HttpResponse(js, content_type="application/javascript")


def _run_sections_with_checks(run: SessionRun):
    sections = (
        Section.objects.filter(strategy=run.strategy)
        .prefetch_related("steps__images")
        .order_by("order", "id")
    )
    checks_by_step_id = {c.step_id: c for c in run.step_checks.select_related("step").all()}
    section_rows = []
    total_steps = 0
    checked_steps = 0

    for section in sections:
        step_rows = []
        steps = section.steps.all().order_by("order", "id")
        for step in steps:
            check = checks_by_step_id.get(step.id)
            images = list(step.images.all())
            step_rows.append({"step": step, "check": check, "images": images, "has_images": bool(images)})
            total_steps += 1
            if check and check.checked:
                checked_steps += 1
        section_rows.append({"section": section, "steps": step_rows})

    return section_rows, total_steps, checked_steps


@login_required
def dashboard_view(request):
    strategies = Strategy.objects.filter(is_active=True).order_by("name")
    recent_runs = (
        SessionRun.objects.filter(user=request.user)
        .select_related("strategy")
        .order_by("-started_at")[:8]
    )
    return render(
        request,
        "journal/dashboard.html",
        {"strategies": strategies, "recent_runs": recent_runs},
    )


@login_required
def strategies_view(request):
    strategies = (
        Strategy.objects.filter(is_active=True)
        .prefetch_related("sections__steps__images")
        .order_by("name")
    )
    return render(request, "journal/strategies.html", {"strategies": strategies})


@login_required
def start_run_view(request):
    if request.method == "POST":
        form = StartSessionRunForm(request.POST)
        if form.is_valid():
            run = form.save(commit=False)
            run.user = request.user
            run.save()

            steps = (
                Step.objects.filter(section__strategy=run.strategy)
                .select_related("section")
                .order_by("section__order", "order", "id")
            )
            StepCheck.objects.bulk_create(
                [StepCheck(session_run=run, step=step, checked=False) for step in steps]
            )
            return redirect("run_detail", run_id=run.id)
    else:
        form = StartSessionRunForm()

    return render(request, "journal/start_run.html", {"form": form})


@login_required
def run_detail_view(request, run_id: int):
    run = get_object_or_404(
        SessionRun.objects.select_related("strategy"),
        pk=run_id,
        user=request.user,
    )

    if request.method == "POST":
        checks = StepCheck.objects.filter(session_run=run).select_related("step")
        now = timezone.now()

        with transaction.atomic():
            for check in checks:
                checkbox_key = f"step_{check.step_id}_checked"
                notes_key = f"step_{check.step_id}_notes"
                should_check = checkbox_key in request.POST
                notes = request.POST.get(notes_key, "").strip()[:300]

                if should_check and not check.checked:
                    check.checked_at = now
                if not should_check:
                    check.checked_at = None

                check.checked = should_check
                check.notes = notes
                check.save(update_fields=["checked", "checked_at", "notes"])

        if "go_review" in request.POST:
            return redirect("run_review", run_id=run.id)
        return redirect("run_detail", run_id=run.id)

    section_rows, total_steps, checked_steps = _run_sections_with_checks(run)
    context = {
        "run": run,
        "section_rows": section_rows,
        "total_steps": total_steps,
        "checked_steps": checked_steps,
    }
    return render(request, "journal/run_detail.html", context)


@login_required
def run_review_view(request, run_id: int):
    run = get_object_or_404(
        SessionRun.objects.select_related("strategy").prefetch_related("step_checks__step__section"),
        pk=run_id,
        user=request.user,
    )
    trade_instance = getattr(run, "trade", None)

    if request.method == "POST":
        review_form = SessionRunReviewForm(request.POST, instance=run)
        trade_form = TradeForm(request.POST, instance=trade_instance)

        if review_form.is_valid():
            with transaction.atomic():
                review = review_form.save(commit=False)
                review.completed = True
                if not review.ended_at:
                    review.ended_at = timezone.now()
                review.save()

                if review.trade_taken:
                    if trade_form.is_valid():
                        trade = trade_form.save(commit=False)
                        trade.session_run = run
                        trade.save()
                    else:
                        context = _review_context(run, review_form, trade_form)
                        return render(request, "journal/run_review.html", context)
                elif trade_instance:
                    trade_instance.delete()

            return redirect("dashboard")
    else:
        review_form = SessionRunReviewForm(instance=run)
        trade_form = TradeForm(instance=trade_instance)

    context = _review_context(run, review_form, trade_form)
    return render(request, "journal/run_review.html", context)


def _review_context(run, review_form, trade_form):
    checks = (
        run.step_checks.select_related("step", "step__section")
        .order_by("step__section__order", "step__order", "id")
    )
    checked_count = sum(1 for c in checks if c.checked)
    return {
        "run": run,
        "checks": checks,
        "checked_count": checked_count,
        "total_count": len(checks),
        "review_form": review_form,
        "trade_form": trade_form,
    }


@login_required
def calendar_view(request):
    """
    Simple monthly calendar. Click a day to open the journal.
    """
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_days = list(cal.itermonthdates(year, month))

    journals = DayJournal.objects.filter(user=request.user, date__year=year, date__month=month)
    journal_days = {j.date for j in journals}

    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1

    context = {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "month_days": month_days,
        "journal_days": journal_days,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "today": today,
    }
    return render(request, "journal/calendar.html", context)

@login_required
def concepts_view(request):
    concepts = Concept.objects.filter(is_active=True).order_by("name")
    return render(request, "journal/concepts.html", {"concepts": concepts})

@login_required
def day_view(request, year: int, month: int, day: int):
    dt = date(year, month, day)
    journal = _get_or_create_journal(request.user, dt)

    if request.method == "POST":
        form = DayJournalForm(request.POST, instance=journal)
        if form.is_valid():
            form.save()
            return redirect("day", year=year, month=month, day=day)
    else:
        form = DayJournalForm(instance=journal)

    concepts = Concept.objects.filter(is_active=True).order_by("name")

    items = JournalSlotItem.objects.filter(journal=journal).select_related("concept")
    by_tf = {tf: [] for tf, _ in Timeframe.choices}
    for it in items:
        by_tf[it.timeframe].append(it)
    timeframe_rows = [
        {"value": tf_value, "label": tf_label, "items": by_tf.get(tf_value, [])}
        for tf_value, tf_label in Timeframe.choices
    ]

    context = {
        "dt": dt,
        "journal": journal,
        "form": form,
        "concepts": concepts,
        "timeframe_rows": timeframe_rows,
    }
    return render(request, "journal/day.html", context)

@login_required
def save_slots_api(request, year: int, month: int, day: int):
    """
    Receives JSON like:
    {
      "slots": {
        "D": [{"concept_id": 1, "note": "..."}, ...],
        "15M": [...]
      }
    }
    Rewrites the slot items for that journal day.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        slots = payload.get("slots", {})
        if not isinstance(slots, dict):
            return HttpResponseBadRequest("Invalid slots payload")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    dt = date(year, month, day)
    journal = _get_or_create_journal(request.user, dt)

    valid_timeframes = {tf for tf, _ in Timeframe.choices}

    with transaction.atomic():
        JournalSlotItem.objects.filter(journal=journal).delete()

        for timeframe, items in slots.items():
            if timeframe not in valid_timeframes:
                continue
            if not isinstance(items, list):
                continue

            for idx, obj in enumerate(items):
                concept_id = obj.get("concept_id")
                note = (obj.get("note") or "")[:240]
                if not concept_id:
                    continue

                concept = get_object_or_404(Concept, pk=int(concept_id), is_active=True)
                JournalSlotItem.objects.create(
                    journal=journal,
                    timeframe=timeframe,
                    concept=concept,
                    order=idx,
                    note=note,
                )

    return JsonResponse({"ok": True})
