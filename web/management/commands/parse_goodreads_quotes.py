import re
from pathlib import Path

from bs4 import BeautifulSoup
from django.core.management import BaseCommand
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager

# https://www.goodreads.com/work/quotes/1494157
from web.models import GoodreadsQuote


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        quotes_dir = Path("data/goodreads_scrape/quotes").absolute().glob("*")
        for file in quotes_dir:
            book_id, page_number = re.match("(\d+)\?page=(\d+)", file.name).groups()
            print(book_id, page_number)

        html_doc = open(file, 'r').read()

        soup = BeautifulSoup(html_doc, 'html.parser')

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()


        quotes = []
        for quote_html in soup.find_all(class_='quoteText'):
            quote = str(quote_html)
            start_quote_index = quote.index('>') + 1
            end_quote_index = quote.index('<br/>')
            quote_text = quote[start_quote_index:end_quote_index].strip()
            quotes.append({
                "text": quote_text,
                "source_book_id": book_id
            })

            with postgres_manager(GoodreadsQuote) as manager:
                manager.on_conflict(['text', 'book'], ConflictAction.NOTHING).bulk_insert(quotes)

        print(GoodreadsQuote.objects.count())
