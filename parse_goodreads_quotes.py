from psqlextra.util import postgres_manager
import re
from pathlib import Path

from IPython import embed
from bs4 import BeautifulSoup

# https://www.goodreads.com/work/quotes/1494157
from web.models import Text

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

    with postgres_manager(Text) as manager:
        manager.on_conflict(['text', 'source_book'], ConflictAction.NOTHING).bulk_insert(quotes)

print(Text.objects.count())