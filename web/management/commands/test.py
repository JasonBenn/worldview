from django.core.management import BaseCommand

from web.models import NotionDocument
from web.services.notion_service.write import scrape


class Command(BaseCommand):
    def handle(self, *args, **options):
        doc = NotionDocument.objects.get(url="https://www.notion.so/jasonbenn/2f61537471d64420b40c263ea48ba9e8?v=823167eafe964ed096c24c0a038f5d2c")
        scrape(doc)
