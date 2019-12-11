from django.core.management.base import BaseCommand

from web.models import GoodreadsAuthor, GoodreadsBook, GoodreadsSeries, NotionDocument


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Goal: save Goodreads entities
        author = GoodreadsAuthor.objects.create(goodreads_id=1, first_name="Greg", last_name="Egan")
        series = GoodreadsSeries.objects.create(goodreads_id=1, title="Unknown Worlds")
        book = GoodreadsBook.objects.create(goodreads_id=1, title="Permutation City", series=series)
        book.authors.set([author])
        book.save()
        print("goodreads reverse relations")
        print(author.books.all())
        print(series.books.all())

        Text.objects.create(text="And then, the craziest shit happened!", source_book=book)
        Text.objects.create(text="Quantum subspace: activated.", source_book=book)
        Text.objects.create(text="Greg Egan writes books.", source_author=author)
        Text.objects.create(text="Insane science fiction.", source_series=series)

        doc = NotionDocument.objects.create(notion_id="ASDF", title="SF imagines the future")
        Text.objects.create(text="Professional imagineers do this all day.", source_notion_document=doc)
        print("texts:")
        print(Text.objects.all())

        # Goal: all highlights that haven't yet been converted
        print("no embeddings:")
        print(Text.objects.filter(embedding__isnull=True))

        # Goal: all highlights that haven't yet been UMAPd
        print("no umap:")
        print(Text.objects.filter(projection__isnull=True))

        # GROUP_BY/average embedding on source?
        texts_by_source = {x: [] for x in list(GoodreadsBook.objects.all()) + list(NotionDocument.objects.all())}
        texts = Text.objects.all().prefetch_related('source_book', 'source_author', 'source_author__books', 'source_series', 'source_series__books', 'source_notion_document')
        for text in texts:
            if text.source_notion_document:
                texts_by_source[text.source_notion_document].append(text)
            if text.source_book:
                texts_by_source[text.source_book].append(text)
            elif text.source_author:
                for book in text.source_author.books.all():
                    texts_by_source[book].append(text)
            elif text.source_series:
                for book in text.source_series.books.all():
                    texts_by_source[book].append(text)

        import ipdb
        ipdb.set_trace()
