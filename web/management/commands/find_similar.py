import numpy as np
from django.core.management import BaseCommand

from web.models import Text
from web.utils import get_similar_text_ids


def get_embedding(text: str):
    return np.random.random(768)


class Command(BaseCommand):
    def handle(self, *args, **options):
        example = "This is a test"
        top_similar_ids = get_similar_text_ids(example)

        print("Most similar to:")
        print(example)
        print()
        for x in Text.objects.filter(id__in=[x[0] for x in top_similar_ids]):
            print(x.text)
