import json
import os
import re
from datetime import date, datetime, timedelta
from enum import Enum
from itertools import islice
from statistics import mean
from typing import List

import numpy as np
from dateutil.parser import parse
from django.contrib.admin.utils import flatten
from django.core.management import BaseCommand
from django.utils.functional import partition
from jinja2 import Template
from networkx import Graph


class Tags(Enum):
    QUESTION = 'Question'
    REFERENCE = 'Reference'
    NOTE = 'Note'
    POST = 'Post'
    SHARES = 'Shares'


class Filepaths(Enum):
    INDEX_HTML = "dashboard/index.html"
    WORD_COUNT_FILEPATH = "dashboard/word_counts.txt"
    NUM_EDGES_FILEPATH = "dashboard/num_edges.txt"
    NUM_SHARES_FILEPATH = "dashboard/num_shares.txt"
    BACKUP_JSON = "data/roam-backup/jason.json"
    DASHBOARD_HTML = 'web/templates/dashboard.html'


def dfs(node):
    if 'children' not in node:
        return
    yield from node['children']
    for child in node['children']:
        yield from dfs(child)


def window(seq, n=2):
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


LINK_REGEX = re.compile('(?:\[\[.*\]\]|#[\w\d]+)')


def parse_links(string: str) -> List[str]:
    matches = re.findall(LINK_REGEX, string)
    return [x.lstrip('#').lstrip('[[').rstrip("]]") for x in matches]


def parse_shares(string: str) -> List[str]:
    return [x for x in string.split(' ') if 'http' in x]


def parse_metrics_file(filename):
    lines = [x.rsplit(' ', 1) for x in open(filename, 'r').read().split('\n')]
    one_week_ago = date.today() - timedelta(days=7)
    words_by_day = {
        parse(date_str).date(): int(word_count) for date_str, word_count in lines if
        parse(date_str).date() >= one_week_ago
    }
    return words_by_day


def squeeze(iter):
    return [x for x in iter if x]


def get_words_metric():
    """
    5 is 500+ words per day. 4 is 400+, etc
    """
    words_by_day = parse_metrics_file(Filepaths.WORD_COUNT_FILEPATH.value)
    score = mean([b - a for a, b in window(words_by_day.values())]) / 100
    return min(round(score, 1), 5.)


def get_connections_metric():
    """
    5 is 5+ connections per day. 4 is 4+, etc
    """
    edges_by_day = parse_metrics_file(Filepaths.NUM_EDGES_FILEPATH.value)
    score = mean([b - a for a, b in window(edges_by_day.values())])
    return min(round(score, 1), 5)


def get_shares_metric():
    """
    5: 1 share per day
    4: 1 share / 2 days
    3: 1 share / 4 days
    2: 1 share / week
    1: 1 share / 2 weeks
    0: less
    """
    shares_by_day = parse_metrics_file(Filepaths.NUM_SHARES_FILEPATH.value)
    if len(shares_by_day) < 2:
        return 0.

    score = mean([b - a for a, b in window(shares_by_day.values())])
    return round(np.interp(score, [0, 1/14, 1/7, 0.25, 0.5, 1], [0, 1, 2, 3, 4, 5]), 1)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        pages = json.loads(open(Filepaths.BACKUP_JSON.value, "r").read())
        graph = Graph()

        # Create nodes
        for page in pages:
            if not ('children' in page and len(page['children'])):
                continue

            for page_type in [Tags.QUESTION.value, Tags.REFERENCE.value, Tags.NOTE.value, Tags.POST.value]:
                matches = [x for x in page['children'] if f'#{page_type}' in x['string']]

                content, metadata = partition(lambda x: '::' in x['string'], matches)

                for line in content:
                    graph.add_node(line['string'], type=page_type, word_count=len(line['string']))

                if len(metadata):
                    graph.add_node(page['title'], data=page, type=page_type)

        num_edges = 0
        word_count = 0
        num_shares = 0

        # Add information to nodes
        for title, data in graph.nodes(data=True):
            if 'data' not in data:
                continue

            # Edges
            links = flatten([parse_links(x['string']) for x in dfs(data['data'])])
            for link in [x for x in links if graph.has_node(x)]:
                graph.add_edge(link, title)
                num_edges += 1

            # Word count
            word_count += sum([len(x['string']) for x in dfs(data['data'])])

            # Shares
            num_shares += len(flatten([parse_shares(x['string']) for x in dfs(data['data']) if f"{Tags.SHARES.value}::" in x['string']]))

        # Save num_edges
        with open(Filepaths.NUM_EDGES_FILEPATH.value, "a") as f:
            f.write(f"\n{datetime.today()} {num_edges}")

        # Save word count
        with open(Filepaths.WORD_COUNT_FILEPATH.value, "a") as f:
            f.write(f"\n{datetime.today()} {word_count}")

        # Save shares
        with open(Filepaths.NUM_SHARES_FILEPATH.value, "a") as f:
            f.write(f"\n{datetime.today()} {num_shares}")

        # Count edges
        for title, data in graph.nodes(data=True):
            data['num_edges'] = len(graph[title])

        # Build index.html
        nodes = list(graph.nodes(data=True))
        questions = [(title, data) for title, data in nodes if data['type'] == Tags.QUESTION.value]
        references = [(title, data) for title, data in nodes if data['type'] == Tags.REFERENCE.value]
        notes = [(title, data) for title, data in nodes if data['type'] == Tags.NOTE.value]
        posts = [(title, data) for title, data in nodes if data['type'] == Tags.POST.value]

        template = Template(open(Filepaths.DASHBOARD_HTML.value).read())
        last_updated = datetime.fromtimestamp(os.path.getmtime(Filepaths.BACKUP_JSON.value))

        with open(Filepaths.INDEX_HTML.value, "w") as f:
            f.write(template.render(
                questions=questions,
                references=references,
                notes=notes,
                posts=posts,
                words_metric=get_words_metric(),
                connections_metric=get_connections_metric(),
                shares_metric=get_shares_metric(),
                last_updated=last_updated
            ))
