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
    notion_id = TextField()
    title = TextField()
    url = TextField()

    def __str__(self):
        return f"<NotionDocument: {self.title}>"


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
