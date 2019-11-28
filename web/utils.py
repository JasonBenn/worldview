import re
from collections import defaultdict
from datetime import datetime
from typing import List

import numpy as np
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


def group_by(iterable, key):
    grouped = defaultdict(list)
    for x in iterable:
        grouped[key(x)].append(x)
    return {k: list(v) for k, v in grouped.items()}


def now() -> datetime:
    return timezone.now()


def get_embedding(text: str):
    return np.random.random(768)


def clean_title(string: str) -> str:
    return "".join([c for c in string.replace(' ', '-') if c.isalnum() or c == '-']).lower()


def remove_newlines(string: str) -> str:
    return string.replace('\n', '<br>')


def asciify(text: str) -> str:
    return re.sub(r'[^\x00-\x7f]', r'', text)


def get_text_chunks(text: str) -> List[str]:
    chunks = []
    # TODO: cut on token boundary: https://spacy.io/usage/linguistic-features#retokenization
    for i in range(len(text) // 512 + 1):
        start_index = i * 512
        end_index = (i+1) * 512
        chunks.append(text[start_index:end_index])
    return chunks
