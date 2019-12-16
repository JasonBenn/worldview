from datetime import datetime
from operator import itemgetter
from typing import Dict
from typing import List
from typing import Union

import ipdb
from django.template import Context
from django.template import Template
from notion.block import BookmarkBlock
from notion.block import BulletedListBlock
from notion.block import CodeBlock
from notion.block import CollectionViewBlock
from notion.block import CollectionViewPageBlock
from notion.block import DividerBlock
from notion.block import EmbedBlock
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
from notion.collection import Collection
from notion.collection import CollectionView

from web.models import NotionDocument
from web.utils import asciify
from web.utils import normalized_notion_url
from web.utils import timeout

NOTION_CLIENT_MEMORY_CACHE = None


@timeout(10)
def get_notion_client() -> NotionClient:
    global NOTION_CLIENT_MEMORY_CACHE
    if NOTION_CLIENT_MEMORY_CACHE is None:
        token_v2 = open('token_v2').read().strip()
        client = NotionClient(token_v2=token_v2, monitor=True)
        NOTION_CLIENT_MEMORY_CACHE = client
    return NOTION_CLIENT_MEMORY_CACHE


def get_db_row_ids(block: Union[CollectionViewPageBlock, CollectionViewBlock]) -> List[str]:
    views_by_num_items = {view: len(view.get()['page_sort']) for view in block.views if ('page_sort' in view.get())}
    view, num_items = max(views_by_num_items.items(), key=itemgetter(1))
    return view.get()['page_sort']


def to_markdown(page: NotionDocument) -> str:
    result = ""
    result += f"# {page.title}\n"
    for child in page.children():
        if isinstance(child, TextBlock):
            result += f"{child.title}\n"
        elif isinstance(child, TodoBlock):
            check = "- [x]" if child.checked else "- [ ]"
            result += f"{check} {child.title}\n"
        elif isinstance(child, PageBlock):
            result += f"<PageBlock: {child.title}>\n"
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
        elif isinstance(child, EmbedBlock):
            result += f"<EMBED: {child.display_source}>\n"
        elif isinstance(child, CodeBlock):
            result += f"```child.title```"
        elif child.type == "table_of_contents":
            continue
        else:
            print(type(child))
            ipdb.set_trace()
    return result


def to_html(page: PageBlock) -> str:
    print("to html")
    notion_client = get_notion_client()
    result = "<div style='text-align: left'>"
    children = list(page.children)
    for i, child in enumerate(children):
        if len(children) > 100:
            import ipdb; ipdb.set_trace()
        if isinstance(child, TextBlock):
            title = child.title
            if "‣" in title:
                title_pieces = child.get('properties')['title']
                link_ids = [x[1][0][1] for x in title_pieces if x[0] == "‣" and x[1][0][0] == 'p']
                for link_id in link_ids:
                    print("getting child link")
                    linked_doc = notion_client.get_block(link_id)
                    linked_doc_url = normalized_notion_url(linked_doc.id)
                    title = title.replace("‣", f"<a href='{linked_doc_url}'>{linked_doc.title}</a>", 1)
            result += f"<p>{title}</p>"
        elif isinstance(child, TodoBlock):
            checked = "checked" if child.checked else ""
            result += f"<div><label>{child.title}<input type='checkbox' {checked}'></label></div>"
        elif isinstance(child, (PageBlock, BookmarkBlock)):
            result += f"<div><a href='{normalized_notion_url(child.id)}'>{child.title}</a></div>"
        elif isinstance(child, DividerBlock):
            result += f"<br/>"
        elif isinstance(child, HeaderBlock):
            result += f"<h1>{child.title}</h1>"
        elif isinstance(child, SubheaderBlock):
            result += f"<h2>{child.title}</h2>"
        elif isinstance(child, SubsubheaderBlock):
            result += f"<h3>{child.title}</h3>"
        elif isinstance(child, BulletedListBlock):
            result += f"<div>{child.title}</div>"
        elif isinstance(child, ToggleBlock):
            result += f"<div>> {child.title}</div>"
        elif isinstance(child, QuoteBlock):
            result += f"<blockquote>{child.title}</blockquote>"
        elif isinstance(child, NumberedListBlock):
            result += f"<div>1. {child.title}</div>"
        elif isinstance(child, CodeBlock):
            result += f"<code>child.title</code>"
        elif isinstance(child, EmbedBlock):
            result += f"<div>EMBED: {child.display_source}</div>"
        elif isinstance(child, ImageBlock):
            url = child.get('properties').get('source')[0][0]
            result += f"<img src='{url}'>"
        elif child.type == "table_of_contents":
            continue
        else:
            result += f"<div>NOT HANDLED: {type(child)} {str(child)}</div>"
        if not isinstance(child, PageBlock) and child.get().get('content'):
            insert_index = i + 1
            # TODO: nest content appropriately.
            for content_id in reversed(child.get().get('content')):
                print("inserting child")
                children.insert(insert_index, notion_client.get_block(content_id))
    return result + "</div>"


def to_plaintext(doc: NotionDocument) -> str:
    result = f"{asciify(doc.title)}\n\n"
    for child in doc.children():
        if isinstance(child, (ImageBlock, DividerBlock)):
            continue
        try:
            result += f"{asciify(child.title)}\n"
        except AttributeError:
            print(type(child))
            ipdb.set_trace()
    return result


def get_schema(block: Union[CollectionView, CollectionViewBlock, Collection]) -> List[Dict]:
    if isinstance(block, (CollectionView, CollectionViewBlock)):
        collection = block.collection
    elif isinstance(block, Collection):
        collection = block
    else:
        raise ValueError("Unknown type")

    return collection.get_schema_properties()


def get_context(page: NotionDocument):
    url = normalized_notion_url(page.id)
    from IPython import embed; embed()
    properties = page.get_all_properties()
    stringified_properties = {}
    for key, value in properties.items():
        if isinstance(value, datetime):
            stringified_properties[key] = value.strftime('%-m/%-d/%y')
        elif isinstance(value, list):
            stringified_properties[key] = ', '.join(value)
        else:
            stringified_properties[key] = str(value)

    return Context({
        "text": to_html(page),
        "title": page.title,
        "url": url,
        "link": f"<a href='{url}'>{page.title}</a>",
        **stringified_properties
    }, autoescape=False)


def make_card_html(doc: NotionDocument) -> str:
    parent = doc.parent_database
    front_template = parent.anki_front_html_template
    back_template = parent.anki_back_html_template

    page = doc.page
    context = get_context(page)
    print(context)

    # TODO: factor out Anki parts
    notion_id = doc.notion_id
    front_html = Template(front_template).render(context)
    back_html = Template(back_template).render(context)
    return f"{ notion_id };{front_html};{back_html}"


def get_all_documents() -> Dict[int, str]:
    return {x['id']: x['text'] for x in NotionDocument.objects.values('id', 'text')}


def crawl_nested_doc(id_or_doc: Union[str, dict], ignore_nested_pages: bool = True) -> dict:
    notion_client = get_notion_client()
    if isinstance(id_or_doc, str):
        # If an ID: fetch
        doc = notion_client.get_block(id_or_doc).get()
    else:
        # If a doc (JSON), continue
        doc = id_or_doc

    # If a whole other page: ignore content (usually)
    if doc.get('type') == 'page' and doc.get('content') and ignore_nested_pages:
        del doc['content']

    title = doc.get('properties', {}).get('title', [])
    unfolded_title = []
    for title_component in title:
        # Manually replace titles for inline links
        is_link = title_component[0] == '‣' and title_component[1][0][0] == 'p'
        if is_link:
            inline_link_id = title_component[1][0][1]
            linked_doc = notion_client.get_block(inline_link_id).get()
            if linked_doc['type'] == 'collection_view_page':
                # TODO: this is a bit gross - links to other kinds of pages have different ways to get titles.
                unfolded_title.append(notion_client.get_collection(linked_doc['collection_id']).get()['name'])
            else:
                unfolded_title.append(linked_doc['properties']['title'])
        else:
            unfolded_title.append(title_component)
    if unfolded_title:
        doc['properties']['title'] = unfolded_title

    content = doc.get('content')
    if content:
        # If there is deeper content to crawl, recurse
        unfolded_content = []
        for child_id in content:
            unfolded_content.append(crawl_nested_doc(child_id))
        doc['content'] = unfolded_content
    return doc
