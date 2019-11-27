import os
import pickle
import re
from pathlib import Path

from pandas import DataFrame
from spacy.lang.en import English
from tqdm import tqdm

from web.services.bert_service.read import get_bert_client

storage_dir = Path("/Users/jasonbenn/.notion-to-anki")
docs_path = storage_dir / "documents"

nlp = English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))
bc = get_bert_client()

encodings = []
doc_titles = os.listdir(docs_path)
for doc_title in tqdm(doc_titles):
    doc = open(docs_path/doc_title).read()
    for para in re.split('\n', doc):
        sentences = [x.text.strip() for x in nlp(para).sents if x.text.strip()]
        if len(sentences):
            vectors = bc.encode(sentences)
            for sentence, vector in zip(sentences, vectors):
                # print(sentence, vector)
                encodings.append({
                    "sentence": sentence,
                    "vector": vector,
                    "document": doc_title
                })


df = DataFrame(encodings)
outputs_dir = Path("/Users/jasonbenn/.notion-to-anki/outputs")
os.makedirs(outputs_dir, exist_ok=True)
pickle.dump(df, open(outputs_dir/'df.pkl', 'wb'))
