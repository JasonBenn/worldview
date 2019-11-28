from typing import Optional

from bert_serving.client import BertClient
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from tqdm import tqdm

from web.models import NotionDocument
from web.models import Text
from web.services.bert_service.read import get_bert_client
from web.services.notion_service.read import *
from web.utils import get_text_chunks


def scrape(root_doc: NotionDocument):
    notion_client = get_notion_client()
    bert_client = get_bert_client()
    block = notion_client.get_block(root_doc.url)

    if block.alive:
        root_doc.notion_id = block.id
        root_doc.title = block.title
        root_doc.save()
    else:
        root_doc.delete()
        return

    if isinstance(block, (CollectionViewPageBlock, CollectionViewBlock)):
        row_ids = get_db_row_ids(block)
        print(f"Scraping: {root_doc.title}")
        for row_id in tqdm(row_ids):
            make_texts(notion_client, bert_client, row_id, parent_doc=root_doc)
    elif isinstance(block, CollectionRowBlock):
        make_texts(notion_client, bert_client, block.id)
    else:
        raise TypeError(f"Unexpected Notion document type: {type(block)}")


def make_texts(notion_client: NotionClient, bert_client: BertClient, notion_id: str, parent_doc: Optional[NotionDocument] = None):
    child_block = notion_client.get_block(notion_id)
    print(child_block)
    if not child_block.alive:
        try:
            NotionDocument.objects.get(notion_id=notion_id).delete()
        except NotionDocument.DoesNotExist:
            pass
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

    text_records = []
    text_chunks = get_text_chunks(to_plaintext(child_block))
    embeddings = bert_client.encode(text_chunks)
    for text_chunk, embedding in zip(text_chunks, embeddings):
        text_records.append({
            "text": text_chunk,
            "source_notion_document": child_doc,
            "embedding": embedding.tolist()
        })

    with postgres_manager(Text) as manager:
        manager.on_conflict(["text", "source_book", "source_notion_document"], ConflictAction.UPDATE).bulk_insert(text_records)

