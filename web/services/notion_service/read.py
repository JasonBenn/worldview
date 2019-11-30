from operator import itemgetter
from typing import List
from typing import Union

import ipdb
from notion.block import BookmarkBlock
from notion.block import BulletedListBlock
from notion.block import CollectionViewBlock
from notion.block import CollectionViewPageBlock
from notion.block import DividerBlock
from notion.block import HeaderBlock
from notion.block import ImageBlock
from notion.block import NumberedListBlock
from notion.block import PageBlock
from notion.block import QuoteBlock
from notion.block import SubheaderBlock
from notion.block import SubsubheaderBlock
from notion.block import TextBlock
from notion.block import TodoBlock
from notion.block import ToggleBlock
from notion.client import NotionClient
from notion.collection import CollectionRowBlock

from web.utils import asciify
from web.utils import clean_title
from web.utils import remove_newlines
from web.utils import timeout


def get_page_url(page_id: str, page_title: str) -> str:
    url = clean_title(page_title) + page_id.replace('-', '')
    return f"notion://www.notion.so/{url}"


def make_card_from_text_page(page_id, page_title) -> str:
    return f"{page_id};<a href='{get_page_url(page_id, page_title)}'>{page_title}</a>;"


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


@timeout(3)
def get_notion_client() -> NotionClient:
    token_v2 = open('token_v2').read().strip()
    return NotionClient(token_v2=token_v2, monitor=True)


def get_db_row_ids(block: Union[CollectionViewPageBlock, CollectionViewBlock]) -> List[str]:
    views_by_num_items = {view: len(view.get()['page_sort']) for view in block.views if ('page_sort' in view.get())}
    view, num_items = max(views_by_num_items.items(), key=itemgetter(1))
    return view.get()['page_sort']


def to_markdown(page: PageBlock) -> str:
    result = ""
    result += f"# {page.title}\n"
    for child in page.children:
        if isinstance(child, TextBlock):
            result += f"{child.title}\n"
        elif isinstance(child, TodoBlock):
            check = "- [x]" if child.checked else "- [ ]"
            result += f"{check} {child.title}\n"
        elif isinstance(child, CollectionRowBlock):
            result += f"<LINK: {child.title}>\n"
        elif isinstance(child, DividerBlock):
            result += f"---\n"
        elif isinstance(child, HeaderBlock):
            result += f"# {child.title}\n"
        elif isinstance(child, SubheaderBlock):
            result += f"## {child.title}\n"
        elif isinstance(child, SubsubheaderBlock):
            result += f"### {child.title}\n"
        elif isinstance(child, BulletedListBlock):
            result += f"* {child.title}\n"
        elif isinstance(child, ToggleBlock):
            result += f"> {child.title}\n"
        elif isinstance(child, QuoteBlock):
            result += f"| {child.title}\n"
        elif isinstance(child, NumberedListBlock):
            result += f"1. {child.title}\n"
        elif isinstance(child, BookmarkBlock):
            result += f"<BOOKMARK: {child.title}>\n"
        else:
            print(type(child))
            ipdb.set_trace()
    return result


def to_plaintext(page: PageBlock) -> str:
    result = f"{asciify(page.title)}\n\n"
    for child in page.children:
        if isinstance(child, (ImageBlock, DividerBlock)):
            continue
        result += f"{asciify(child.title)}\n"
    return result
