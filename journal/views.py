import calendar
import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DayJournalForm
from .models import Concept, DayJournal, JournalSlotItem, Timeframe

def _get_or_create_journal(user, dt: date) -> DayJournal:
    journal, _ = DayJournal.objects.get_or_create(user=user, date=dt)
    return journal

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

    context = {
        "dt": dt,
        "journal": journal,
        "form": form,
        "concepts": concepts,
        "timeframes": Timeframe.choices,
        "by_tf": by_tf,
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
