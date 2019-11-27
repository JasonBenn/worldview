from functools import partial
from operator import itemgetter
from typing import List
from typing import Tuple

import numpy as np
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import ManyToManyField
from django.db.models import Model
from django.db.models import TextField

from web.utils import get_embedding
from web.utils import now


class BaseModel(Model):
    created_at = DateTimeField(default=now, editable=False)
    updated_at = DateTimeField(default=now, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = now()
        super().save(*args, **kwargs)


class GoodreadsEntity(BaseModel):
    goodreads_id = IntegerField()
    url = TextField()

    class Meta:
        abstract = True


class GoodreadsSeries(GoodreadsEntity):
    title = TextField()

    def __str__(self):
        return f"<GoodreadsSeries: {self.title}>"


class GoodreadsAuthor(GoodreadsEntity):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)

    def __str__(self):
        return f"<GoodreadsAuthor: {self.first_name} {self.last_name}>"


class GoodreadsBook(GoodreadsEntity):
    title = TextField()
    series = ForeignKey(GoodreadsSeries, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="books")
    authors = ManyToManyField(GoodreadsAuthor, related_name="books")

    def __str__(self):
        return f"<GoodreadsBook: {self.title}>"


class GoodreadsUser(GoodreadsEntity):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)

    def __str__(self):
        return f"<GoodreadsUser: {self.first_name} {self.last_name}>"


class GoodreadsShelf(GoodreadsEntity):
    books = ManyToManyField(GoodreadsBook)

    def __str__(self):
        return f"<GoodreadsShelf: {len(self.books)} books>"


class NotionDocument(BaseModel):
    notion_id = TextField(null=True, blank=True)
    title = TextField(null=True, blank=True)
    url = TextField()

    def __str__(self):
        content = self.title or "[not yet scraped] " + self.url
        return f"<NotionDocument: {content}>"


class Text(BaseModel):
    class Meta:
        unique_together = ('text', 'source_book', 'source_notion_document')

    text = TextField()
    embedding = JSONField(null=True, blank=True)
    projection = JSONField(null=True, blank=True)
    source_author = ForeignKey(GoodreadsAuthor, null=True, blank=True, on_delete=models.DO_NOTHING)
    source_series = ForeignKey(GoodreadsSeries, null=True, blank=True, on_delete=models.DO_NOTHING)
    source_book = ForeignKey(GoodreadsBook, null=True, blank=True, on_delete=models.DO_NOTHING)
    source_notion_document = ForeignKey(NotionDocument, null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        maybe_ellipsis = "..." if len(self.text) > 25 else ""
        return f"<Text: {self.text[:25]}{maybe_ellipsis}>"


def get_similar_text_ids(example: str) -> List[Tuple[int, float]]:
    compute_similarity = partial(np.dot, get_embedding(example))
    embeddings = {x['id']: x['embedding'] for x in
                  Text.objects.filter(embedding__isnull=False).values('id', 'embedding')}
    similarities = {text_id: compute_similarity(embedding) for text_id, embedding in embeddings.items()}
    # TODO: get anything more similar than some sensible threshold
    top_similar_ids = sorted(similarities.items(), key=itemgetter(1), reverse=True)[:5]
    return top_similar_ids
