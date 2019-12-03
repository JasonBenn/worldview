import re

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import BooleanField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import ManyToManyField
from django.db.models import Model
from django.db.models import TextField

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


class NotionDatabase(BaseModel):
    url = TextField()
    notion_id = TextField(null=True, blank=True, unique=True)
    title = TextField(null=True, blank=True)
    schema = JSONField(null=True, blank=True)
    anki_front_html_template = TextField(null=True, blank=True)
    anki_back_html_template = TextField(null=True, blank=True)

    def clean(self):
        if not self.schema or not (self.anki_front_html_template or self.anki_back_html_template):
            return True
        valid_properties = {x['slug'] for x in self.schema}
        for label, template in {"front": self.anki_front_html_template, "back": self.anki_back_html_template}.items():
            used_properties = set(re.findall("{{([\w_]+)}}", template or ""))
            if not all(x in valid_properties for x in used_properties):
                raise ValidationError(f"Anki {label} format is invalid! Can't use: {used_properties - valid_properties}")

    def __str__(self):
        if self.title is None:
            title = "[not yet scraped] " + self.url
        elif self.title == "":
            title = "[empty title]"
        else:
            title = self.title
        return f"<NotionDatabase: {title}>"


class NotionDocument(BaseModel):
    url = TextField()
    notion_id = TextField(null=True, blank=True, unique=True)
    parent_database = ForeignKey(NotionDatabase, on_delete=models.CASCADE)
    title = TextField(null=True, blank=True)
    embedding = JSONField(null=True, blank=True)

    def __str__(self):
        if self.title is None:
            title = "[not yet scraped] " + self.url
        elif self.title == "":
            title = "[empty title]"
        else:
            title = self.title
        return f"<NotionDocument: {title}>"


class Text(BaseModel):
    class Meta:
        unique_together = ('text', 'source_book', 'source_notion_document')

    text = TextField()
    embedding = JSONField(null=True, blank=True)
    projection = JSONField(null=True, blank=True)
    source_author = ForeignKey(GoodreadsAuthor, null=True, blank=True, on_delete=models.CASCADE)
    source_series = ForeignKey(GoodreadsSeries, null=True, blank=True, on_delete=models.CASCADE)
    source_book = ForeignKey(GoodreadsBook, null=True, blank=True, on_delete=models.CASCADE)
    source_notion_document = ForeignKey(NotionDocument, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        maybe_ellipsis = "..." if len(self.text) > 25 else ""
        return f"<Text: {self.text[:25]}{maybe_ellipsis}>"
