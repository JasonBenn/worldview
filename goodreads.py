from urllib.parse import urlencode
import os

import goodreads_api_client as gr
import oauth2 as oauth

from dotenv import load_dotenv
import xmltodict

load_dotenv()
GOODREADS_KEY = os.getenv('GOODREADS_KEY')
GOODREADS_SECRET = os.getenv('GOODREADS_SECRET')
gr_client = gr.Client(developer_key=GOODREADS_KEY)


def get_book():
    book = gr_client.Book.show('18883652')  # Permutation City
    # book = gr_client.Book.show('1128434')  # The Witcher
    # keys_wanted = ['id', 'title', 'isbn']
    # reduced_book = {k:v for k, v in book.items() if k in keys_wanted}
    print(book['title'])
    print(book['description'])

    series_id = book['series_works']['series_work']['series']['id']
    series = gr_client.Series.show(series_id)  # Subjective Cosomology
    print(series['title'])
    print(series['description'])

    # This is sometimes a list, sometimes a single author?
    author_id = book['authors']['author']['id']
    # author_ids = [x['id'] for x in book['authors']['author'] if x['role'] != 'Translator']
    # author_id = author_ids[0]
    author = gr_client.Author.show(author_id)  # Greg Egan
    print(author['about'])


user_id = "6481511"

shelves_data = gr_client.Shelf.list(user_id)
shelves = shelves_data['user_shelf']

for shelf in shelves:
    shelf_name = shelf['name']
    if shelf_name == 'to-read':
        break

shelf_id = shelf['id']['#text']
print(shelf_name)
print(shelf['book_count']['#text'])
print(shelf_id)

consumer = oauth.Consumer(key=GOODREADS_KEY, secret=GOODREADS_SECRET)
token = oauth.Token(GOODREADS_KEY, GOODREADS_SECRET)

oauth_client = oauth.Client(consumer, token)

page = 1
shelf_books_url = f'http://www.goodreads.com/review/list/{shelf_id}.xml'

# headers = {'content-type': 'application/x-www-form-urlencoded'}
query = {
    "v": 2,
    "key": GOODREADS_KEY,
    "shelf": "read",
    "per_page": 200,
    "page": page,
}
params = urlencode(query)
response, content = oauth_client.request(shelf_books_url + "?" + params, 'GET')
print(response['status'])
print(content)
# response, content = oauth_client.request(shelf_books_url, 'GET', body, headers)
# if response['status'] != '200':
# raise Exception('Failure status: %s for page ' % response['status'] + page)
#    else:
#        print 'Page loaded!'
print(response)
data = xmltodict.parse(content)
datum = data['GoodreadsResponse']['reviews']['review'][0]
book = datum['book']
print(book['title'])
print(book['description'])
print(book['link'])
from IPython.core.debugger import set_trace; set_trace()
