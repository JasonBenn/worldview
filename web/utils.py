from collections import defaultdict
from datetime import datetime

import numpy as np
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
