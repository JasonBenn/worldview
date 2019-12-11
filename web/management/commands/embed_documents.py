from operator import itemgetter

import numpy as np
from django.core.management import BaseCommand
from tqdm import tqdm

from web.models import NotionDocument
from web.utils import group_by


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Text.objects.filter(source_notion_document__bookmarked__isnull=False)
        texts = Text.objects.filter(source_notion_document__bookmarked__isnull=False).values('source_notion_document_id', 'embedding', 'text')
        grouped_texts = group_by(texts, key=itemgetter('source_notion_document_id'))
        documents_by_id = {x.id: x for x in NotionDocument.objects.filter(id__in=grouped_texts.keys())}

        documents_with_embeddings = []
        for doc_id, text_group in tqdm(grouped_texts.items()):
            document = documents_by_id[doc_id]
            embeddings, weights = zip(*[(x['embedding'], len(x['text'])) for x in text_group])
            document.embedding = np.average(embeddings, axis=0, weights=weights).tolist()
            documents_with_embeddings.append(document)
        NotionDocument.objects.bulk_update(documents_with_embeddings, ['embedding'])
