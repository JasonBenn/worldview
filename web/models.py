from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import IntegerField, TextField, ForeignKey, Model, ManyToManyField, DateTimeField

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


class Text(BaseModel):
    text = TextField()
    embedding = JSONField(null=True, blank=True)
    projection = JSONField(null=True, blank=True)
    source = ForeignKey(GoodreadsEntity, null=True, blank=True, on_delete=models.DO_NOTHING)


class GoodreadsSeries(GoodreadsEntity):
    title = TextField()


class GoodreadsAuthor(GoodreadsEntity):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)


class GoodreadsBook(GoodreadsEntity):
    title = TextField()
    series = ForeignKey(GoodreadsSeries, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="books")
    authors = ManyToManyField(GoodreadsAuthor, null=True, blank=True, related_name="books")


class GoodreadsUser(GoodreadsEntity):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)


class GoodreadsShelf(GoodreadsEntity):
    books = ManyToManyField(GoodreadsBook)


class NotionDocument(BaseModel):
    notion_id = TextField()
    title = TextField()
    url = TextField()


class SyncEvent(BaseModel):
    # Sync to Anki?
    # Pull from Notion?
    # Scrape Goodreads shelf?
    pass