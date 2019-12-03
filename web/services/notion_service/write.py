from typing import Optional

from bert_serving.client import BertClient
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from tqdm import tqdm

from web.models import NotionDatabase
from web.models import NotionDocument
from web.models import Text
from web.services.notion_service.read import *
from web.utils import get_text_chunks


def scrape_self(doc: Union[NotionDatabase, NotionDocument]):
    """Verify the Notion doc is still alive, scrape some info about it"""
    import threading
    print(threading.current_thread())
    print("Scraping self")
    notion_client = get_notion_client()
    block = notion_client.get_block(doc.url)
    if not block.alive:
        doc.delete()
        return

    doc.notion_id = block.id
    doc.title = block.title
    print("Getting schema")
    if isinstance(doc, NotionDatabase):
        doc.schema = get_schema(block)
    print("Saving")
    doc.save()
    print("Done")


def scrape_children(db: NotionDatabase):
    import threading
    print(threading.current_thread())
    notion_client = get_notion_client()
    block = notion_client.get_block(db.url)
    scrape_self(db)

    print("Getting BERT")
    bert_client = None  # get_bert_client()
    print("Got BERT")
    if isinstance(block, (CollectionViewPageBlock, CollectionViewBlock)):
        row_ids = get_db_row_ids(block)
        print(f"Scraping: {db.title}")
        for row_id in tqdm(row_ids):
            make_texts(notion_client, row_id, parent_db=db, bert_client=bert_client)
    # elif isinstance(block, CollectionRowBlock):
    #     make_texts(notion_client, bert_client, block.id)
    else:
        raise TypeError(f"Unexpected Notion document type: {type(block)}")


def make_texts(notion_client: NotionClient, notion_id: str, parent_db: NotionDatabase, bert_client: Optional[BertClient] = None):
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
        "url": child_block.get_browseable_url(),
        "parent_database": parent_db
    }

    child_doc, created = NotionDocument.objects.get_or_create(
        notion_id=notion_id,
        defaults=defaults
    )

    text_records = []
    text_chunks = get_text_chunks(to_plaintext(child_block))
    if bert_client:
        embeddings = bert_client.encode(text_chunks).tolist()
    else:
        embeddings = [None] * len(text_chunks)
    for text_chunk, embedding in zip(text_chunks, embeddings):
        text_records.append({
            "text": text_chunk,
            "source_notion_document": child_doc,
            "embedding": embedding
        })

    with postgres_manager(Text) as manager:
        manager.on_conflict(["text", "source_book", "source_notion_document"], ConflictAction.UPDATE).bulk_insert(text_records)

