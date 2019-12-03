from functools import partial
from operator import itemgetter

import numpy as np
from django.core.management import BaseCommand

from web.models import NotionDocument
from web.services.bert_service.read import get_bert_client
from web.services.notion_service.read import get_notion_client
from web.services.notion_service.read import to_plaintext
from web.utils import cosine_distance
from web.utils import get_text_chunks


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('notion_url')

    def handle(self, *args, **kwargs):
        url = kwargs['notion_url']
        notion_client = get_notion_client()
        # block = notion_client.get_block(url)
        # text = to_plaintext(block)
        # print(text)
        # from IPython import embed; embed()

        # block  # <CollectionRowBlock (id='36c730c4-58dd-4355-837f-e747baa2991f', title='Status is zero sum, but we can invent many status hierarchies')>
        # content_ids = block.get().get('content')
        # ['c4e385af-3020-428c-8cf1-b7e90f61f7fd',
        #  '5204fe65-b657-47b5-a7d6-172f44b8184a']
        # notion_client.get_block(content_ids[0])  # <TextBlock (id='c4e385af-3020-428c-8cf1-b7e90f61f7fd', title='Balance with ‣.')>
        # text_block = notion_client.get_block(content_ids[1])  # <TextBlock (id='5204fe65-b657-47b5-a7d6-172f44b8184a')>
        print("printing ")
        stuff1 = notion_client.get_record_data('block', 'c4e385af-3020-428c-8cf1-b7e90f61f7fd')
        text = notion_client.get_block('c4e385af-3020-428c-8cf1-b7e90f61f7fd')
        if "‣" in text.title:
            text.get().properties()

        title_pieces = text.get('properties')['title']
        title_link_piece = title_pieces[1]
        assert title_link_piece[0] == "‣" and title_link_piece[1][0][0] == "p", title_link_piece
        ougoing_link_id = title_link_piece[1][0][1]

        print(stuff1)
        from IPython import embed; embed()
        # stuff = notion_client.get_record_data('block', '5204fe65-b657-47b5-a7d6-172f44b8184a')
        # print(stuff)
        # In [34]: text_block.get()
        # Out[34]:
        # {'id': '5204fe65-b657-47b5-a7d6-172f44b8184a',
        #  'version': 6,
        #  'type': 'text',
        #  'created_by': '3c6b94c0-680d-4476-90bd-7b76b5af5fb0',
        #  'created_time': 1575155100000,
        #  'last_edited_by': '3c6b94c0-680d-4476-90bd-7b76b5af5fb0',
        #  'last_edited_time': 1575155100000,
        #  'parent_id': '36c730c4-58dd-4355-837f-e747baa2991f',
        #  'parent_table': 'block',
        #  'alive': True,
        #  'created_by_table': 'notion_user',
        #  'created_by_id': '3c6b94c0-680d-4476-90bd-7b76b5af5fb0',
        #  'last_edited_by_table': 'notion_user',
        #  'last_edited_by_id': '3c6b94c0-680d-4476-90bd-7b76b5af5fb0'}

        # looking for:
        # <CollectionRowBlock (id='6e3725e0-5aba-4612-9763-aad0335f0398', title='Early career failure is extremely motivating')>
        # notion_client.get_block("https://www.notion.so/jasonbenn/Early-career-failure-is-extremely-motivating-6e3725e05aba46129763aad0335f0398")
