import os
from pathlib import Path

import spacy
from django.core.management import BaseCommand
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
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
        nlp = spacy.load("en_core_web_sm")
        lemmatized_texts = []
        print("lemmatizing")
        for text in tqdm(texts):
            lemmatized_tokens = []
            tokens = nlp(text)
            for token in tokens:
                lemmatized_tokens.append(token.lemma_)

            lemmatized_texts.append(" ".join(lemmatized_tokens))

        print("tf-idf'ing")
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(lemmatized_texts)

        n_neighbors = 10
        min_dist = 0.5
        print("umapping")
        reducer = UMAP(n_neighbors=n_neighbors, min_dist=min_dist)
        projections = reducer.fit_transform(vectors)

        embeddables = []
        for doc, text, projection in zip(docs, texts, projections.tolist()):
            embeddables.append({
                "text": text,
                "source": doc,
                "embedding_type": EmbeddingType.LEMMATIZED_TF_IDF,
                "projection": projection
            })

        with postgres_manager(Document) as manager:
            manager.on_conflict(['source', 'embedding_type'], ConflictAction.UPDATE).bulk_insert(embeddables)


