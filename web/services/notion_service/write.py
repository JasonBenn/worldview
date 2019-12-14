import os
from typing import Optional

from django.conf import settings
from django.db.models import Q
from tqdm import tqdm

from web.models import NotionDatabase
from web.services.notion_service.read import *
from web.utils import now


def scrape_notion_db(doc: Union[NotionDatabase, NotionDocument]):
    """Verify the Notion doc is still alive, scrape some info about it"""
    print("Scraping self")
    notion_client = get_notion_client()
    page = notion_client.get_block(doc.url)
    if not page.alive:
        doc.delete()
        return

    doc.notion_id = page.id
    doc.title = page.title
    print("Getting schema")
    if isinstance(doc, NotionDatabase):
        doc.schema = get_schema(page)
    print("Saving")
    doc.save()
    print("Done")


def scrape_children(db: NotionDatabase):
    notion_client = get_notion_client()
    page = notion_client.get_block(db.url)
    scrape_notion_db(db)

    if isinstance(page, (CollectionViewPageBlock, CollectionViewBlock)):
        row_ids = get_db_row_ids(page)
        print(f"Scraping: {db.title}")
        for row_id in tqdm(row_ids):
            # TODO: when to update, when to not update?
            # existing_doc = NotionDocument.objects.filter(Q(url=url) | Q(notion_id=notion_id))
            # if not update_if_exists and existing_doc.count():
            #     return existing_doc.first()

            scrape_notion_document(row_id, db)
    else:
        raise TypeError(f"Unexpected Notion document type: {type(page)}")


def scrape_notion_document(notion_id: str, parent_db: NotionDatabase) -> Optional[NotionDocument]:
    notion_client = get_notion_client()
    page = notion_client.get_block(notion_id)
    url = page.get_browseable_url()

    uncrawled_doc = {"page": page.get(), "content": [x.get() for x in page.children]}
    json = crawl_nested_doc(uncrawled_doc)
    if not json['page']['alive']:
        return None

    doc, created = NotionDocument.objects.update_or_create(notion_id=notion_id, url=url, defaults={"json": json, "parent_database": parent_db})
    return doc


def export_db_to_anki(db: NotionDatabase):
    card_htmls = []
    for doc in NotionDocument.objects.filter(parent_database=db):
        card_htmls.append(make_card_html(doc))
    filepath = settings.BASE_DOCUMENT_DIR / clean_title(db.title)
    with open(filepath, "w") as f:
        print("\n".join(card_htmls), file=f)
    db.updated_at = now()
    db.save()


def export_to_anki(doc: NotionDocument):
    card_html = make_card_html(doc)
    base_dir = settings.BASE_DOCUMENT_DIR / "individual_cards"
    os.makedirs(base_dir, exist_ok=True)
    filepath = base_dir / clean_title(doc.title)
    with open(filepath, "w") as f:
        print(card_html, file=f)
    print(filepath)
    doc.updated_at = now()
    doc.save()
