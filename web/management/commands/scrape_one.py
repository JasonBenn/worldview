from django.core.management import BaseCommand

from web.models import NotionDocument
from web.services.notion_service.write import scrape_notion_document
from web.utils import restore_notion_id_hyphens


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('flat_notion_id')

    def handle(self, *args, **kwargs):
        notion_id = restore_notion_id_hyphens(kwargs['flat_notion_id'])
        print(notion_id)
        doc = NotionDocument.objects.get(notion_id=notion_id)
        scrape_notion_document(doc.notion_id, doc.parent_database)
        print(NotionDocument.objects.get(notion_id=notion_id).json['page']['properties'])
