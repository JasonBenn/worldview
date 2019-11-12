import os
import sys

from notion.block import ImageBlock
from notion.client import NotionClient


def get_page_url(page_id: str, page_title: str) -> str:
    clean_title = "".join([c for c in page_title.replace(' ', '-') if c.isalnum() or c == '-'])
    page_url = clean_title + page_id.replace('-', '')
    return f"notion://www.notion.so/{page_url}"


def make_card_from_page(page_id, page_title) -> str:
    return f"{page_id};<a href='{get_page_url(page_id, page_title)}'>{page_title}</a>;"


def make_image_card_from_page(page_id, page_title, image_url, compression) -> str:
    return f"{page_id};<img src='{image_url}'>;<a href='{get_page_url(page_id, page_title)}'>{page_title}</a><br><p>{compression}</p>"


token_v2 = "b9d79f1c69e7c498da57eba93e26d34903808c76ab90d2760d340f473db40a607c8325a393c84de178c044f9661b7cc4fe3efceadbe72b6755bf859764df46f103de466695b6673c0bd420c7a214"

export_type = sys.argv[1]
page_url = sys.argv[2]
assert export_type in ["text", "photo"]

client = NotionClient(token_v2=token_v2)

page = client.get_block(page_url)
collection = client.get_collection(page.get('collection_id'))
collection.refresh()
rows = collection.get_rows()

cards = []
for row in rows:
    if export_type == "photo":
        images = [x for x in row.children if isinstance(x, ImageBlock)]
        if not any(images):
            continue
        cards.append(make_image_card_from_page(row.id, row.title, images[0].source, row.get_all_properties()['compression']))
    elif export_type == "text":
        cards.append(make_card_from_page(row.id, row.title))

storage_dir = "/Users/jasonbenn/.notion-to-anki"
os.makedirs(storage_dir, exist_ok=True)
filename = page.title.lower().replace(' ', '-')
with open(f"{storage_dir}/{filename}", "w") as f:
    for card in cards:
        print(card, file=f)
