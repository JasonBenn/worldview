import os

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
            scrape_notion_document(row_id, db)
    else:
        raise TypeError(f"Unexpected Notion document type: {type(page)}")


def scrape_notion_document(notion_id: str, parent_db: NotionDatabase) -> None:
    notion_client = get_notion_client()
    page = notion_client.get_block(notion_id)
    url = page.get_browseable_url()
    if NotionDocument.objects.filter(Q(url=url) | Q(notion_id=notion_id)).count():
        return
    uncrawled_doc = {"page": page.get(), "content": [x.get() for x in page.children]}
    json = crawl_nested_doc(uncrawled_doc)
    NotionDocument.objects.create(json=json, notion_id=notion_id, url=url, parent_database=parent_db)


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
