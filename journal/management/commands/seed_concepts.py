from django.core.management.base import BaseCommand
from journal.models import Concept

DEFAULT_CONCEPTS = [
    "BOS",
    "CHoCH",
    "FVG",
    "iFVG",
    "Order Block (OB)",
    "Breaker Block",
    "Mitigation Block",
    "Liquidity Sweep",
    "Equal Highs (EQH)",
    "Equal Lows (EQL)",
    "Premium/Discount",
    "Daily High/Low",
    "Weekly High/Low",
    "Previous Day High (PDH)",
    "Previous Day Low (PDL)",
    "Overnight High",
    "Overnight Low",
    "Killzone Confluence",
    "Market Structure Shift (MSS)",
    "Displacement",
    "Imbalance",
    "Judas Swing",
    "OTE",
    "Round Number / Psychological Level",
]

class Command(BaseCommand):
    help = "Seed default ICT concepts into Concept library"

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_CONCEPTS:
            obj, was_created = Concept.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} concepts."))
