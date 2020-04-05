import glob
import os
import re
from datetime import date, datetime, timedelta
from enum import Enum
from itertools import islice
from statistics import mean
from typing import List
from uuid import UUID

import attr
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
    FLASHCARD = 'Flashcard'


LINK_REGEX = re.compile(r'(?:\[\[.*\]\]|#[\w\d]+)')
BULLET_REGEX_STR = r'^\s*- '
BULLET_REGEX = re.compile(BULLET_REGEX_STR)
TWO_SIDED_FLASHCARD_FRONT_REGEX = re.compile(BULLET_REGEX_STR + r"(.*)#" + Tags.FLASHCARD.value + " ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:: )?(.*)", re.I | re.DOTALL)
TWO_SIDED_FLASHCARD_BACK_REGEX = re.compile(BULLET_REGEX_STR + r"(.*)", re.DOTALL)
CLOZE_FLASHCARD_REGEX = re.compile(r"\{(.*)\}", re.I | re.DOTALL)
BASE_DIR = "/Users/jasonbenn/code/worldview/"


class Filepaths(Enum):
    INDEX_HTML = BASE_DIR + "dashboard/index.html"
    WORD_COUNT_FILEPATH = BASE_DIR + "dashboard/word_counts.txt"
    NUM_EDGES_FILEPATH = BASE_DIR + "dashboard/num_edges.txt"
    NUM_SHARES_FILEPATH = BASE_DIR + "dashboard/num_shares.txt"
    BACKUP_DIR = BASE_DIR + "data/roam-backup/*"
    DASHBOARD_HTML = BASE_DIR + 'web/templates/dashboard.html'
    LAST_BUILT = BASE_DIR + 'data/dashboard_built_at.txt'


def window(seq, n=2):
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result


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


@attr.s
class Flashcard:
    uuid: UUID = attr.ib()
    front: str = attr.ib()
    back: str = attr.ib()


def get_bulleted_lines(lines: List[str]):
    bulleted_lines = []
    max_index = len(lines)
    bulleted_indexes_generator = (i for i, x in enumerate(lines) if re.match(BULLET_REGEX, x))
    prev_index = next(bulleted_indexes_generator, max_index)

    while prev_index != max_index:
        next_index = next(bulleted_indexes_generator, max_index)
        bulleted_line = '\n'.join(lines[prev_index:next_index])
        bulleted_lines.append(bulleted_line)
        prev_index = next_index

    return bulleted_lines


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print(datetime.today(), "Building dashboard...")
        pages = {os.path.basename(x).rstrip('.md'): open(x, 'r').read() for x in glob.glob(Filepaths.BACKUP_DIR.value) if os.path.isfile(x)}
        graph = Graph()
        flashcards: List[Flashcard] = []

        # Create nodes
        for page_title, page in pages.items():
            lines = squeeze(page.split('\n'))
            if not len(lines):
                continue

            for page_type in [Tags.QUESTION.value, Tags.REFERENCE.value, Tags.NOTE.value, Tags.POST.value]:
                matches = [x for x in lines if f'#{page_type}' in x]

                content, metadata = partition(lambda x: '::' in x, matches)

                for line in content:
                    # This node is a single line.
                    graph.add_node(line.strip().lstrip('- '), type=page_type, word_count=len(line.split(' ')))

                if len(metadata):
                    # This node is a page.
                    graph.add_node(page_title, lines=lines, type=page_type)

            # Find flashcards
            bulleted_lines = get_bulleted_lines(lines)
            num_bulleted_lines = len(bulleted_lines)
            for i, line in enumerate(bulleted_lines):
                if f"#{Tags.FLASHCARD.value}" in line:
                    print(line)
                    is_num_lines_long_enough = i + 1 < num_bulleted_lines
                    well_formatted_flashcard_front = re.match(TWO_SIDED_FLASHCARD_FRONT_REGEX, line)
                    is_cloze = re.findall(CLOZE_FLASHCARD_REGEX, line)

                    if is_cloze:
                        print("TODO: cloze cards", line)
                        continue

                    if not is_num_lines_long_enough or not well_formatted_flashcard_front:
                        print(f"Flashcard front improperly formatted: {line}")
                        continue

                    next_line = bulleted_lines[i + 1]
                    next_line_is_indented = re.match(BULLET_REGEX, line).span()[1] < re.match(BULLET_REGEX, next_line).span()[1]

                    if next_line_is_indented:
                        front_1, flashcard_uuid, front_2 = well_formatted_flashcard_front.groups()
                        front = (front_1.strip() + " " + front_2.strip()).strip()
                        back = re.match(TWO_SIDED_FLASHCARD_BACK_REGEX, next_line).group(1).strip()
                        flashcards.append(Flashcard(uuid=flashcard_uuid, front=front, back=back))
                    else:
                        print(f"Flashcard improperly formatted (next line not indented): {line}\n{next_line}")

        num_edges = 0
        word_count = 0
        num_shares = 0

        # Add information to nodes
        for title, data in graph.nodes(data=True):
            if 'lines' not in data:
                continue

            # Edges
            links = flatten([parse_links(x) for x in data['lines']])
            for link in [x for x in links if graph.has_node(x)]:
                graph.add_edge(link, title)
                num_edges += 1

            # Word count
            word_count += sum([len(x.split(' ')) for x in data['lines']])  # TODO FIXME

            # Shares
            num_shares += len(flatten([parse_shares(x) for x in data['lines'] if f"{Tags.SHARES.value}::" in x]))

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
        last_updated = datetime.fromtimestamp(os.path.getmtime(glob.glob(Filepaths.BACKUP_DIR.value)[0]))

        with open(Filepaths.INDEX_HTML.value, "w") as f:
            f.write(template.render(
                questions=questions,
                references=references,
                notes=notes,
                posts=posts,
                words_metric=get_words_metric(),
                connections_metric=get_connections_metric(),
                shares_metric=get_shares_metric(),
                last_updated=last_updated,
                last_built=open(Filepaths.LAST_BUILT.value).read()
            ))
        print(datetime.today(), "Done building dashboard!")
