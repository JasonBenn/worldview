from pathlib import Path

from django.core.management import BaseCommand
from django.template import Context, Template
from notion.collection import CollectionRowBlock

from web.models import NotionDocument
from web.services.notion_service.read import get_notion_client, get_page_url, to_html
from web.utils import remove_newlines


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        page_url = "https://www.notion.so/jasonbenn/B-references-A-cf825e3a79c141a5ad2f49d0c6ca3640"

        client = get_notion_client()

        page = client.get_block(page_url)

        storage_dir = Path("/Users/jasonbenn/.notion-to-anki")
        docs_path = storage_dir / "test.txt"

        doc = NotionDocument.objects.get(notion_id=page.id)
        parent = doc.parent_database

        front_template = parent.anki_front_html_template
        back_template = parent.anki_back_html_template

        def get_context(page: CollectionRowBlock):
            url = get_page_url(page.id, page.title)
            return Context({
                "text": to_html(page),
                "title": page.title,
                "url": url,
                "link": f"<a href='{url}'>{page.title}</a>",
                **page.get_all_properties()
            }, autoescape=False)

        context = get_context(page)
        front_html = Template(front_template).render(context)
        back_html = Template(back_template).render(context)

        card_html = f"{doc.notion_id};{front_html};{back_html}"
        print(card_html)

        with open(docs_path, "w") as f:
            print(card_html, file=f)


# TODO: move to HTML in admin page, then include in seed command
def make_image_card_from_page(page_id, page_title, image_url, compression) -> str:
    return f"{page_id};<img src='{image_url}'>;<a href='{get_page_url(page_id, page_title)}'>{page_title}</a><br><p>{compression}</p>"


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

