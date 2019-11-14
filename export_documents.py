from notion.client import NotionClient

from utils import to_markdown

token_v2 = open('token_v2').read().strip()
client = NotionClient(token_v2=token_v2, monitor=True)

worldview_url = "https://www.notion.so/jasonbenn/Flashcards-make-memory-a-choice-5f0f818c3cf846e288e638f3339881ce"
page = client.get_block(worldview_url)
thing = to_markdown(page)
import ipdb; ipdb.set_trace()