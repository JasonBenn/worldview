from functools import partial
from operator import itemgetter

import numpy as np
from django.core.management import BaseCommand

from web.models import Text
from web.services.bert_service.read import get_bert_client
from web.services.notion_service.read import get_notion_client
from web.services.notion_service.read import to_plaintext
from web.utils import cosine_distance
from web.utils import get_text_chunks


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('notion_url')

    def handle(self, *args, **kwargs):
        url = kwargs['notion_url']
        notion_client = get_notion_client()
        print("Getting doc")
        block = notion_client.get_block(url)
        print("SIMILAR TO:", block.title)
        text = to_plaintext(block)
        text_chunks = get_text_chunks(text)
        bert_client = get_bert_client()
        print("Embedding")
        embeddings = bert_client.encode(text_chunks)
        document_embedding = np.average(embeddings, axis=0, weights=[len(x) for x in text_chunks])  # weighted avg by chunk length
        compute_similarity = partial(cosine_distance, document_embedding)

        print("Finding similar")
        relevant_texts = Text.objects\
            .filter(embedding__isnull=False)\
            .exclude(source_notion_document__parent_notion_document__title="People")\
            .values('id', 'embedding')
        embeddings = {x['id']: x['embedding'] for x in relevant_texts}
        similarities = {text_id: compute_similarity(embedding) for text_id, embedding in embeddings.items()}
        top_similar_ids = sorted(similarities.items(), key=itemgetter(1), reverse=True)

        ids, similarities = zip(*top_similar_ids)
        similarities = np.ravel(similarities)
        print(f'similarity range: {max(similarities):.3f} - {min(similarities):.3f}')

        # starting_index = len(ids) - 5
        starting_index = 0
        most_similar_text = Text.objects\
            .filter(id__in=ids[:5])\
            .values('text', 'source_notion_document__title', 'source_notion_document__parent_notion_document__title')

        for i, similar_text in enumerate(most_similar_text):
            print('-------------------')
            print(f'similarity: {similarities[(starting_index + i)]:.3f}')
            print()
            parent_title = similar_text['source_notion_document__parent_notion_document__title']
            source_title = similar_text['source_notion_document__title']
            title = f"{parent_title} > {source_title}" if parent_title else source_title
            print('#', title)
            print(similar_text['text'])
