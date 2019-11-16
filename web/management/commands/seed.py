from django.core.management.base import BaseCommand

from web.server.models import GoodreadsAuthor, GoodreadsSeries, GoodreadsBook, Text, NotionDocument


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Goal: save Goodreads entities
        author = GoodreadsAuthor.objects.create(id=1, first_name="Greg", last_name="Egan")
        series = GoodreadsSeries.objects.create(id=1, title="Unknown Worlds")
        book = GoodreadsBook.objects.create(id=1, title="Permutation City", series=series, author=author)
        print("goodreads reverse relations")
        print(author.books.all())
        print(series.books.all())

        Text.objects.create("And then, the craziest shit happened!", source=book)
        Text.objects.create("Quantum subspace: activated.", source=book)
        Text.objects.create("Greg Egan writes books.", source=author)
        Text.objects.create("Insane science fiction.", source=series)

        doc = NotionDocument.objects.create(notion_id="ASDF", title="SF imagines the future")
        Text.objects.create("Professional imagineers do this all day.", source=doc)
        print("texts:")
        print(Text.objects.all())

        # Goal: all highlights that haven't yet been converted
        print("no embeddings:")
        print(Text.objects.filter(embedding__isnull=True))

        # Goal: all highlights that haven't yet been UMAPd
        print("no umap:")
        print(Text.objects.filter(projection__isnull=True))

        # GROUP_BY/average embedding on source?
        import ipdb
        ipdb.set_trace()
