import numpy as np
from django.core.management import BaseCommand
from tqdm import tqdm

from web.models import Text


def get_embedding(text: str):
    return np.random.random(768)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('notion_url')

    def handle(self, *args, **kwargs):
        notion_url = kwargs['notion_url']
        print(notion_url)
        need_embeddings = list(Text.objects.filter(embedding__isnull=True))
        print(f"Computing embeddings for {len(need_embeddings)} Texts.")
        for text in tqdm(need_embeddings):
            text.embedding = get_embedding(text.text).tolist()
            text.save()
