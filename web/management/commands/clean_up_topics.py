from django.core.management import BaseCommand

from web.models import NotionDocument
from web.services.notion_service.write import scrape_notion_document
from web.utils import preprocess_docs_to_words


class Command(BaseCommand):
    def handle(self, *args, **options):
        doc = NotionDocument.objects.get(url="https://www.notion.so/5901c87500d34106894bf15e50f359a1")
        # doc = scrape_notion_document(doc.notion_id, doc.parent_database)
        result = preprocess_docs_to_words([doc.to_plaintext()])

        print(result)
