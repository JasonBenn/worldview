import re
from enum import IntEnum

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import ManyToManyField
from django.db.models import Model
from django.db.models import TextField
from polymorphic.models import PolymorphicModel

from web.utils import asciify
from web.utils import flatten
from web.utils import now


class Timestampable(Model):
    created_at = DateTimeField(default=now, editable=False)
    updated_at = DateTimeField(default=now, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = now()
        super().save(*args, **kwargs)


class Source(PolymorphicModel):
    json = JSONField()


class EmbeddingType(IntEnum):
    # https://medium.com/@bencleary/using-enums-as-django-model-choices-96c4cbb78b2e
    TF_IDF = 0
    BERT = 1

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Document(Timestampable, Model):
    class Meta:
        unique_together = [('source', 'embedding_type')]

    text = TextField()
    source = ForeignKey(Source, on_delete=models.CASCADE)
    embedding = JSONField(null=True, blank=True)
    embedding_type = IntegerField(choices=EmbeddingType.choices(), null=True, blank=True)
    projection = JSONField(null=True, blank=True)

    def __str__(self):
        return self.text[:125]


class Goodreadsable(Model):
    goodreads_id = IntegerField()
    url = TextField()

    class Meta:
        abstract = True


class GoodreadsSeries(Timestampable, Goodreadsable, Source):
    title = TextField()

    def __str__(self):
        return f"<GoodreadsSeries: {self.title}>"


class GoodreadsAuthor(Timestampable, Goodreadsable, Source):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)

    def __str__(self):
        return f"<GoodreadsAuthor: {self.first_name} {self.last_name}>"


class GoodreadsBook(Timestampable, Goodreadsable, Source):
    title = TextField()
    series = ForeignKey(GoodreadsSeries, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="books")
    authors = ManyToManyField(GoodreadsAuthor, related_name="books")

    def __str__(self):
        return f"<GoodreadsBook: {self.title}>"


class GoodreadsShelf(Timestampable, Goodreadsable, Source):
    books = ManyToManyField(GoodreadsBook)

    def __str__(self):
        return f"<GoodreadsShelf: {len(self.books)} books>"


class GoodreadsQuote(Timestampable, Goodreadsable, Source):
    book = ForeignKey(GoodreadsBook, on_delete=models.CASCADE)

    def __str__(self):
        return f"<GoodreadsQuote: {self.text:100}>"


class GoodreadsUser(Timestampable, Goodreadsable, Model):
    first_name = TextField()
    last_name = TextField(null=True, blank=True)

    def __str__(self):
        return f"<GoodreadsUser: {self.first_name} {self.last_name}>"


SPECIAL_PROPERTIES = {
    "text": ...,
    "url": ...,
    "title": ...,
    "link": ...,
}


class NotionDatabase(Timestampable, Model):
    url = TextField(help_text="<strong>Required.</strong>")
    notion_id = TextField(null=True, blank=True, unique=True)
    title = TextField(null=True, blank=True)
    schema = JSONField(null=True, blank=True, help_text="<strong>Do not fill.</strong> This field is automatically populated by the 'scrape self' action on the Databases overview page.")
    anki_front_html_template = TextField(null=True, blank=True, help_text="""\
    <strong>Prerequisite</strong>: "Schema" field must be populated.<br><br>
    These templates are used to create an Anki card for each record in this database. The syntax is HTML plus Notion database properties as "slugs" (the property name, but lower cased and snake cased). Slugs should also be surrounded by double curly braces.<br>
    See Schema JSON above for valid slugs (you'll need to scrape this DB first).<br>
    Several special properties are also valid slugs: <code>{{text}}</code> (the full contents of the note), <code>{{url}}</code> (the Notion URL of the note), <code>{{title}}</code>, and <code>{{link}}</code> (a shortcut for <code>&lt;a href="{{url}}&gt;{{title}}&lt;/a&gt;</code>").<br><br>
    Example: <code>&lt;div&gt;{{link}}&lt;br&gt;{{created_at}}&lt;/div&gt;</code>
    """)
    anki_back_html_template = TextField(null=True, blank=True, help_text="Same syntax as above.")

    def clean(self):
        has_template = self.anki_front_html_template or self.anki_back_html_template

        if not has_template:
            return True

        if not self.schema and has_template:
            raise ValidationError("Can't ensure a template is valid until after the DB's schema has been scraped! Enter just the URL, go back to the main page, and choose the scrape self option.")

        if ";" in self.anki_front_html_template or ";" in self.anki_back_html_template:
            raise ValidationError("Please don't use semicolons - they're used to delimit Anki fields.")

        if "\n" in self.anki_front_html_template or ";" in self.anki_back_html_template:
            raise ValidationError("Please don't use newlines - Anki will think each line is a separate flashcard.")

        valid_properties = {x['slug'] for x in self.schema} | set(SPECIAL_PROPERTIES.keys())
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


class NotionDocument(Timestampable, Source):
    url = TextField(unique=True)
    notion_id = TextField(null=True, blank=True, unique=True)
    parent_database = ForeignKey(NotionDatabase, on_delete=models.CASCADE)

    def __str__(self):
        if self.title == "":
            title = "[empty title]"
        else:
            title = self.title
        return f"<NotionDocument: {title}>"

    @property
    def title(self) -> str:
        if self.json is None:
            # Not yet scraped
            return self.url
        else:
            return ''.join(flatten(self.json['page'].get('properties', {}).get('title', ['[no title]'])))

    def to_plaintext(self) -> str:
        result = f"{asciify(self.title)}\n\n"
        content = self.json['content']
        for i, child in enumerate(content):
            # If no content, just print a newline.
            title = ''.join([x for x in flatten(child.get('properties', {}).get('title', [])) if not isinstance(x, dict) and not len(x) == 1])

            if child.get('content'):
                insert_index = i + 1
                # TODO: nest content appropriately.
                for nested_content in reversed(child.get('content')):
                    content.insert(insert_index, nested_content)

            result += f"{asciify(title)}\n"
        return result
