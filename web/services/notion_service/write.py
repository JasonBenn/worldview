from typing import Optional

from notion.block import CollectionViewBlock
from notion.block import CollectionViewPageBlock
from tqdm import tqdm

from web.models import NotionDocument
from web.models import Text
from web.services.notion_service.read import *
from web.utils import get_text_chunks


def scrape(root_doc: NotionDocument):
    client = get_notion_client()
    block = client.get_block(root_doc.url)
    root_doc.notion_id = block.id
    root_doc.title = block.title
    root_doc.save()
    if not block.alive:
        root_doc.delete()

    if isinstance(block, (CollectionViewPageBlock, CollectionViewBlock)):
        row_ids = get_db_row_ids(block)
        print(f"Scraping: {root_doc.title}")
        for row_id in tqdm(row_ids):
            make_texts(client, row_id, parent_doc=root_doc)
    elif isinstance(block, CollectionRowBlock):
        make_texts(client, block.id)
    else:
        raise TypeError(f"Unexpected Notion document type: {type(block)}")


def make_texts(client: NotionClient, notion_id: str, parent_doc: Optional[NotionDocument] = None):
    child_block = client.get_block(notion_id)
    if not child_block.alive:
        NotionDocument.objects.get(notion_id=notion_id).delete()
        return

    defaults = {
        "title": child_block.title,
        "url": child_block.get_browseable_url()
    }
    if parent_doc is not None:
        defaults["parent_notion_document"] = parent_doc
    child_doc, created = NotionDocument.objects.get_or_create(
        notion_id=notion_id,
        defaults=defaults
    )
    for text_chunk in get_text_chunks(to_plaintext(child_block)):
        Text.objects.get_or_create(
            text=text_chunk,
            source_notion_document=child_doc
        )
