import numpy as np
from django.core.management import BaseCommand
from tqdm import tqdm

from web.models import Text
from web.services.notion_service.read import get_client


def get_embedding(text: str):
    return np.random.random(768)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('notion_url')

    def handle(self, *args, **kwargs):
        notion_url = kwargs['notion_url']
        print(notion_url)
        client = get_client()
        block = client.get_block(notion_url)
        print(block)

        from IPython import embed; embed()
        need_embeddings = list(Text.objects.filter(embedding__isnull=True))
        print(f"Computing embeddings for {len(need_embeddings)} Texts.")
        for text in tqdm(need_embeddings):
            text.embedding = get_embedding(text.text).tolist()
            text.save()
