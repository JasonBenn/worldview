from collections import defaultdict
from datetime import datetime
from functools import partial
from operator import itemgetter
from typing import List, Tuple

import numpy as np
from django.utils import timezone

from web.management.commands.find_similar import get_embedding
from web.models import Text


def group_by(iterable, key):
    grouped = defaultdict(list)
    for x in iterable:
        grouped[key(x)].append(x)
    return {k: list(v) for k, v in grouped.items()}


def now() -> datetime:
    return timezone.now()


def get_similar_text_ids(example: str) -> List[Tuple[int, float]]:
    compute_similarity = partial(np.dot, get_embedding(example))
    embeddings = {x['id']: x['embedding'] for x in
                  Text.objects.filter(embedding__isnull=False).values('id', 'embedding')}
    similarities = {text_id: compute_similarity(embedding) for text_id, embedding in embeddings.items()}
    # TODO: get anything more similar than some sensible threshold
    top_similar_ids = sorted(similarities.items(), key=itemgetter(1), reverse=True)[:5]
    return top_similar_ids