import json
import os
import re
from datetime import datetime
from typing import List

from django.contrib.admin.utils import flatten
from django.core.management import BaseCommand
from django.utils.functional import partition
from jinja2 import Template
from networkx import Graph


def dfs(node):
    if 'children' not in node:
        return
    yield from node['children']
    for child in node['children']:
        yield from dfs(child)


LINK_REGEX = re.compile('(?:\[\[.*\]\]|#[\w\d]+)')


def parse_links(string: str) -> List[str]:
    matches = re.findall(LINK_REGEX, string)
    return [x.lstrip('#').lstrip('[[').rstrip("]]") for x in matches]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        backup_filepath = "data/roam-backup/jason.json"
        pages = json.loads(open(backup_filepath, "r").read())
        graph = Graph()

        # Create nodes
        for page in pages:
            if not ('children' in page and len(page['children'])):
                continue

            for page_type in ["Question", "Reference", "Note", "Post"]:
                matches = [x for x in page['children'] if '#' + page_type in x['string']]

                content, metadata = partition(lambda x: '::' in x['string'], matches)

                for line in content:
                    graph.add_node(line['string'], type=page_type)

                if len(metadata):
                    graph.add_node(page['title'], data=page, type=page_type)

        # Create edges
        for title, data in graph.nodes(data=True):
            if 'data' not in data:
                continue
            links = flatten([parse_links(x['string']) for x in dfs(data['data'])])
            for link in [x for x in links if graph.has_node(x)]:
                graph.add_edge(link, title)

        # Count edges
        for title, data in graph.nodes(data=True):
            data['num_edges'] = len(graph[title])

        # Build index.html
        nodes = list(graph.nodes(data=True))
        questions = [(title, data) for title, data in nodes if data['type'] == 'Question']
        references = [(title, data) for title, data in nodes if data['type'] == 'Reference']
        notes = [(title, data) for title, data in nodes if data['type'] == 'Note']
        posts = [(title, data) for title, data in nodes if data['type'] == 'Post']

        template = Template(open('web/templates/dashboard.html').read())
        last_updated = datetime.fromtimestamp(os.path.getmtime(backup_filepath))

        with open("dashboard/index.html", "w") as f:
            f.write(template.render(questions=questions, references=references, notes=notes, posts=posts, last_updated=last_updated))
