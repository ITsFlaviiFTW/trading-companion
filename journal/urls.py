from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("strategies/", views.strategies_view, name="strategies"),
    path("runs/start/", views.start_run_view, name="start_run"),
    path("runs/<int:run_id>/", views.run_detail_view, name="run_detail"),
    path("runs/<int:run_id>/review/", views.run_review_view, name="run_review"),
    path("concepts/", views.concepts_view, name="concepts"),
    path("legacy/calendar/", views.calendar_view, name="calendar"),
    path("day/<int:year>/<int:month>/<int:day>/", views.day_view, name="day"),
    path("api/day/<int:year>/<int:month>/<int:day>/save-slots/", views.save_slots_api, name="save_slots_api"),
]
