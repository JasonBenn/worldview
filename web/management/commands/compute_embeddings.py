import numpy as np
from django.core.management import BaseCommand
from tqdm import tqdm

from web.models import Text


def get_embedding(text: str):
    return np.random.random(768)


class Command(BaseCommand):
    def handle(self, *args, **options):
        need_embeddings = list(Text.objects.filter(embedding__isnull=True))
        print(f"Computing embeddings for {len(need_embeddings)} Texts.")
        for text in tqdm(need_embeddings):
            text.embedding = get_embedding(text.text).tolist()
            text.save()
