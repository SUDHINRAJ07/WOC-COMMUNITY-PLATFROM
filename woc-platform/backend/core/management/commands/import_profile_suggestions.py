import gzip
import json
from collections import Counter
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import ProfileSuggestion


class Command(BaseCommand):
    help = 'Import the bundled India college/location and profile vocabulary snapshot. No network access or affiliation changes.'

    def handle(self, *args, **options):
        path = Path(__file__).resolve().parents[2] / 'data' / 'profile-suggestions.json.gz'
        with gzip.open(path, 'rt', encoding='utf-8') as source:
            records = json.load(source)
        with transaction.atomic():
            ProfileSuggestion.objects.bulk_create(
                [ProfileSuggestion(**row) for row in records], batch_size=500,
                update_conflicts=True, unique_fields=['kind', 'source_id'],
                update_fields=['name', 'search_name', 'state', 'district', 'source'],
            )
        self.stdout.write(self.style.SUCCESS(f'Imported {len(records)} reference records: {dict(Counter(r["kind"] for r in records))}'))
