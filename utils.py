import ipdb
from notion.block import BulletedListBlock
from notion.block import DividerBlock
from notion.block import HeaderBlock
from notion.block import NumberedListBlock
from notion.block import PageBlock
from notion.block import QuoteBlock
from notion.block import SubheaderBlock
from notion.block import SubsubheaderBlock
from notion.block import TextBlock
from notion.block import TodoBlock
from notion.block import ToggleBlock
from notion.collection import CollectionRowBlock


def to_markdown(page: PageBlock) -> str:
    result = ""
    result += page.title
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
        else:
            print(type(child))
            ipdb.set_trace()
    return result
