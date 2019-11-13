import os
import sys

# from notion.block import ImageBlock
from notion.client import NotionClient


def get_page_url(page_id: str, page_title: str) -> str:
    clean_title = "".join([c for c in page_title.replace(' ', '-') if c.isalnum() or c == '-'])
    page_url = clean_title + page_id.replace('-', '')
    return f"notion://www.notion.so/{page_url}"


def make_card_from_text_page(page_id, page_title) -> str:
    return f"{page_id};<a href='{get_page_url(page_id, page_title)}'>{page_title}</a>;"


def make_image_card_from_page(page_id, page_title, image_url, compression) -> str:
    return f"{page_id};<img src='{image_url}'>;<a href='{get_page_url(page_id, page_title)}'>{page_title}</a><br><p>{compression}</p>"


def remove_newlines(string: str) -> str:
    return string.replace('\n', '<br>')


def make_card_from_person_page(row) -> str:
    full_name = row.first_name.split(' ')[0] + ' ' + row.last_name
    next_question = remove_newlines(row.next_question_to_ask_them)
    return f"{row.id};" \
        f"<a href='{get_page_url(row.id, row.title)}'>{full_name}</a>;" \
        f"<b>Compression:</b> {row.compression}<br>" \
        f"<b>Next Q:</b> {next_question}<br>" \
        f"<b>Groups:</b> {', '.join(row.groups)}<br>" \
        f"<b>Location:</b> {', '.join(row.location)}<br>" \
        f"<b>Edited:</b> {row.edited.strftime('%-m/%-d/%y')}<br>" \
        f"<b>Added:</b> {row.added.strftime('%-m/%-d/%y')}"


export_type = sys.argv[1]
page_url = sys.argv[2]
assert export_type in ["text", "people"]

token_v2 = open('token_v2').read().strip()
client = NotionClient(token_v2=token_v2, monitor=True)

page = client.get_block(page_url)
collection = client.get_collection(page.get('collection_id'))
collection.refresh()
rows = collection.get_rows()
if not len(rows):
    print("Empty rows?")
    import ipdb; ipdb.set_trace()

cards = []
for row in rows:
    if export_type == "people":
        # images = [x for x in row.children if isinstance(x, ImageBlock)]
        # if not any(images):
        #     continue
        cards.append(make_card_from_person_page(row))
    elif export_type == "text":
        cards.append(make_card_from_text_page(row.id, row.title))

storage_dir = "/Users/jasonbenn/.notion-to-anki"
os.makedirs(storage_dir, exist_ok=True)
filename = page.title.lower().replace(' ', '-')
with open(f"{storage_dir}/{filename}", "w") as f:
    for card in cards:
        print(card, file=f)
