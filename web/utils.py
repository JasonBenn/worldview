import errno
import os
import re
import signal
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import List
import numpy as np

from django.utils import timezone


def group_by(iterable, key):
    grouped = defaultdict(list)
    for x in iterable:
        grouped[key(x)].append(x)
    return {k: list(v) for k, v in grouped.items()}


def now() -> datetime:
    return timezone.now()


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
        end_index = (i + 1) * 512
        chunks.append(text[start_index:end_index])
    return chunks


class TimeoutError(Exception):
    pass


def timeout(seconds=5, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def cosine_distance(a: np.array, b: np.array) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def flatten(arr):
    for i in arr:
        if isinstance(i, list):
            yield from flatten(i)
        else:
            yield i
