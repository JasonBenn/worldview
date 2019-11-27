import os
import sys
# from notion.block import ImageBlock
from pathlib import Path

from tqdm import tqdm

from web.services.notion_service.read import to_plaintext
from web.services.notion_service.read import get_notion_client
from web.services.notion_service.read import get_db_row_urls
from web.services.notion_service.read import make_card_from_person_page
from web.services.notion_service.read import make_card_from_text_page

export_type = sys.argv[1]
page_url = sys.argv[2]
assert export_type in ["text", "people", "document"]

client = get_notion_client()

page = client.get_block(page_url)
rows = []

for x in tqdm(get_db_row_urls(page)):
    rows.append(client.get_block(x))

storage_dir = Path("/Users/jasonbenn/.notion-to-anki")
docs_path = storage_dir / "documents"
os.makedirs(docs_path, exist_ok=True)

cards = []
for row in tqdm(rows):
    if export_type == "people":
        # images = [x for x in row.children if isinstance(x, ImageBlock)]
        # if not any(images):
        #     continue
        cards.append(make_card_from_person_page(row))
    elif export_type == "text":
        cards.append(make_card_from_text_page(row.id, row.title))
    elif export_type == "document":
        open(docs_path / row.id, 'w').write(to_plaintext(row))


filename = page.title.lower().replace(' ', '-')
with open(storage_dir/filename, "w") as f:
    for card in cards:
        print(card, file=f)
