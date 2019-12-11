from django.core.management import BaseCommand

from web.services.bert_service.read import get_bert_client
from web.services.notion_service.read import get_notion_client
from web.services.notion_service.read import to_plaintext


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('notion_url')

    def handle(self, *args, **kwargs):
        notion_url = kwargs['notion_url']
        print(notion_url)
        notion_client = get_notion_client()
        block = notion_client.get_block(notion_url)
        print(block)
        text = to_plaintext(block)
        bert_client = get_bert_client()
        embedding = bert_client.encode([text])
        print(embedding)
        # need_embeddings = list(Text.objects.filter(embedding__isnull=True))
        # print(f"Computing embeddings for {len(need_embeddings)} Texts.")
        # for text in tqdm(need_embeddings):
        #     text.embedding = get_embedding(text.text).tolist()
        #     text.save()
