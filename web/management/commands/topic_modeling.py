from pprint import pprint

from django.core.management import BaseCommand

from web.models import NotionDocument
from web.utils import make_topic_model
from web.utils import preprocess_docs_to_words


class Command(BaseCommand):
    def handle(self, *args, **options):
        notion_docs = NotionDocument.objects.all()
        text_docs = [x.to_plaintext() for x in notion_docs]
        words = preprocess_docs_to_words(text_docs)
        lda_model, coherence_score = make_topic_model(words, num_topics=7)
        pprint(lda_model.print_topics())
        print(f"Coherence score: {coherence_score}")
        from IPython import embed; embed()
