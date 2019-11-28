from django.core.management import BaseCommand

from web.models import NotionDocument
from web.services.notion_service.write import scrape


class Command(BaseCommand):
    def handle(self, *args, **options):
        doc = NotionDocument.objects.get(url="https://www.notion.so/c8aa7aaf5f794d619c77f3fc1e4d8218")
        scrape(doc)
