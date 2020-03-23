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
        data = json.loads(open(backup_filepath, "r").read())
        graph = Graph()

        # Create nodes
        for node in data:
            if not ('children' in node and len(node['children'])):
                continue

            tagged_children = [x for x in node['children'] if '#Note' in x['string']]
            inline_children, node_descriptors = partition(lambda x: '::' in x['string'], tagged_children)

            for inline_node in inline_children:
                graph.add_node(inline_node['string'])

            if len(node_descriptors):
                graph.add_node(node['title'], data=node)

        # Create edges
        for node_title, node in graph.nodes(data=True):
            if 'data' not in node:
                continue
            links = flatten([parse_links(x['string']) for x in dfs(node['data'])])
            for link in [x for x in links if graph.has_node(x)]:
                graph.add_edge(link, node_title)

        # Count edges
        for node_title, node in graph.nodes(data=True):
            node['num_edges'] = len(graph[node_title])

        # Build index.html
        notes = list(graph.nodes(data=True))
        template = Template(open('web/templates/dashboard.html').read())
        last_updated = datetime.fromtimestamp(os.path.getmtime(backup_filepath))
        with open("build/index.html", "w") as f:
            f.write(template.render(notes=notes, last_updated=last_updated))
