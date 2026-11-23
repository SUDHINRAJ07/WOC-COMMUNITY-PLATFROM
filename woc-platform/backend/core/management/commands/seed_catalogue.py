import json
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import Program
class Command(BaseCommand):
 help='Load the clearly labelled sample WOC catalogue. Does not create user accounts.'
 def handle(self,*args,**kwargs):
  path=Path(__file__).resolve().parents[4]/'frontend'/'data'/'catalog.json'
  for item in json.loads(path.read_text(encoding='utf-8')):
   slug=item.pop('slug');Program.objects.update_or_create(slug=slug,defaults={**item,'sample':True,'verified':False})
  self.stdout.write(self.style.SUCCESS('Sample catalogue loaded.'))
