import os
from pathlib import Path

from django.core.management import BaseCommand
from sense2vec import Sense2Vec

MODEL_DIRPATH = Path("/Users/jasonbenn/.worldview/models")
MODEL_PATH = MODEL_DIRPATH / 'tfidf.joblib'
os.makedirs(MODEL_DIRPATH, exist_ok=True)


class Command(BaseCommand):
    def handle(self, *args, **options):

        s2v = Sense2Vec().from_disk("/Users/jasonbenn/data/s2v_old")
        query = "natural_language_processing|NOUN"
        assert query in s2v
        vector = s2v[query]
        freq = s2v.get_freq(query)
        most_similar = s2v.most_similar(query, n=3)
        from IPython import embed; embed()
        # https://github.com/explosion/sense2vec

        # docs = NotionDocument.objects.all()
        # texts = [x.to_plaintext() for x in docs]
        # nlp = spacy.load("en_core_web_sm")
        # lemmatized_texts = []
        # print("lemmatizing")
        # for text in tqdm(texts):
        #     lemmatized_tokens = []
        #     tokens = nlp(text)
        #     for token in tokens:
        #         lemmatized_tokens.append(token.lemma_)
        #
        #     lemmatized_texts.append(" ".join(lemmatized_tokens))
