from django.urls import path
from . import views

urlpatterns = [
    path("", views.calendar_view, name="calendar"),
    path("concepts/", views.concepts_view, name="concepts"),
    path("day/<int:year>/<int:month>/<int:day>/", views.day_view, name="day"),
    path("api/day/<int:year>/<int:month>/<int:day>/save-slots/", views.save_slots_api, name="save_slots_api"),
]
