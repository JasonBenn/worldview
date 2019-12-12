import os
from pathlib import Path

from django.core.management import BaseCommand
from joblib import dump, load
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from sklearn.feature_extraction.text import TfidfVectorizer
from umap import UMAP

from web.models import Document
from web.models import EmbeddingType
from web.models import NotionDocument


MODEL_DIRPATH = Path("/Users/jasonbenn/.worldview/models")
MODEL_PATH = MODEL_DIRPATH / 'tfidf.joblib'
os.makedirs(MODEL_DIRPATH, exist_ok=True)


class Command(BaseCommand):
    def handle(self, *args, **options):
        docs = NotionDocument.objects.all()
        texts = [x.to_plaintext() for x in docs]

        if os.path.exists(MODEL_PATH):
            vectorizer = load(MODEL_PATH)
        else:
            # TODO: lemmatize
            vectorizer = TfidfVectorizer()
            vectorizer.fit_transform(texts)
            dump(vectorizer, MODEL_PATH)

        vectors = vectorizer.transform(texts)

        n_neighbors = 10
        min_dist = 0.5
        reducer = UMAP(n_neighbors=n_neighbors, min_dist=min_dist)
        projections = reducer.fit_transform(vectors)

        embeddables = []
        for doc, text, projection in zip(docs, texts, projections.tolist()):
            embeddables.append({
                "text": text,
                "source": doc,
                "embedding_type": EmbeddingType.TF_IDF,
                "projection": projection
            })
        with postgres_manager(Document) as manager:
            manager.on_conflict(['source', 'embedding_type'], ConflictAction.NOTHING).bulk_insert(embeddables)
