import glob
import json
import os
import re
import time
from datetime import date, datetime, timedelta
from enum import Enum
from itertools import islice
from re import Pattern
from statistics import mean
from typing import List
from typing import Optional
from typing import Tuple
from uuid import UUID

import attr
import numpy as np
from dateutil.parser import parse
from django.contrib.admin.utils import flatten
from django.core.management import BaseCommand
from django.utils.functional import partition
from jinja2 import Template
from networkx import Graph
import urllib.request
import urllib.parse as urlparse
from urllib.parse import unquote


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
SANS_BULLET_REGEX = re.compile(BULLET_REGEX_STR + r"(.*)", re.DOTALL)
FLASHCARD_FRONT_REGEX = re.compile(BULLET_REGEX_STR + r"(.*)#" + Tags.FLASHCARD.value + " ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:: )?(.*)", re.I | re.DOTALL)
ANKI_DECK_TAG_REGEX = re.compile(r"(.*)\[\[Anki: (.*)\]\](.*)")
CLOZE_REGEX = re.compile(r"\{(.*?)\}", re.DOTALL)
MD_IMAGE_REGEX = re.compile('!\[.*?\]\((.*?)\)')


IS_PROD = False if os.uname().sysname == "Darwin" else True
HOME_DIR = "/home/flock/" if IS_PROD else "/Users/jasonbenn/code/"
PROJECT_DIR = HOME_DIR + "worldview/"
DASHBOARD_DIR = PROJECT_DIR + "dashboard/"


DEFAULT_DECK_NAME = "roam"


class Filepaths(Enum):
    INDEX_HTML = DASHBOARD_DIR + "index.html"
    WORD_COUNT_FILEPATH = DASHBOARD_DIR + "word_counts.txt"
    NUM_EDGES_FILEPATH = DASHBOARD_DIR + "num_edges.txt"
    NUM_SHARES_FILEPATH = DASHBOARD_DIR + "num_shares.txt"
    DASHBOARD_HTML = PROJECT_DIR + 'web/templates/dashboard.html'
    LAST_BUILT = PROJECT_DIR + 'data/dashboard_built_at.txt'
    BACKUP_DIR = HOME_DIR + "roam-notes/markdown/*"


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


def parse_metrics_file(filename, days_ago=7):
    lines = [x.rsplit(' ', 1) for x in open(filename, 'r').read().split('\n') if x]
    one_week_ago = date.today() - timedelta(days=days_ago)
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
    data_points = [b - a for a, b in window(words_by_day.values())]
    if not len(data_points):
        return 0
    score = mean(data_points) / 100
    return min(round(score, 1), 5.)


def get_connections_metric():
    """
    5 is 5+ connections per day. 4 is 4+, etc
    """
    edges_by_day = parse_metrics_file(Filepaths.NUM_EDGES_FILEPATH.value)
    data_points = [b - a for a, b in window(edges_by_day.values())]
    if not len(data_points):
        return 0
    score = mean(data_points)
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
    data_points = [b - a for a, b in window(shares_by_day.values())]
    if not len(data_points):
        return 0
    score = mean(data_points)
    return round(np.interp(score, [0, 1/14, 1/7, 0.25, 0.5, 1], [0, 1, 2, 3, 4, 5]), 1)


@attr.s
class AnkiFlashcard:
    uuid: UUID = attr.ib()
    front: str = attr.ib()
    deck: str = attr.ib()

    def to_add_note_json(self):
        raise NotImplementedError

    def to_update_note_fields_json(self, anki_id):
        raise NotImplementedError

    @staticmethod
    def maybe_download_media_files_and_convert(content: str) -> str:
        for url in re.findall(MD_IMAGE_REGEX, content):
            roam_filename = unquote(urlparse.urlparse(url).path.split('/')[-1]).split('/')[-1]
            if not make_anki_request('retrieveMediaFile', filename=roam_filename):
                make_anki_request('storeMediaFile', filename=roam_filename, url=url)
            content = re.sub(MD_IMAGE_REGEX, f'<img src="{roam_filename}">', content, 1)
        return content


@attr.s
class TwoSidedFlashcard(AnkiFlashcard):
    back: str = attr.ib()

    def to_add_note_json(self):
        return {
            "deckName": self.deck,
            "modelName": "Basic with ID",
            "fields": {
                "ID": self.uuid,
                "Front": self.front,
                "Back": self.back
            },
            "tags": []
        }

    def to_update_note_fields_json(self, anki_id):
        return {
            "id": anki_id,
            "modelName": "Basic with ID",
            "fields": {
                "ID": self.uuid,
                "Front": self.front,
                "Back": self.back
            },
            "tags": []
        }


@attr.s
class ClozeFlashcard(AnkiFlashcard):
    def to_add_note_json(self):
        return {
            "deckName": self.deck,
            "modelName": "Cloze with ID",
            "fields": {
                "ID": self.uuid,
                "Text": self.front,
            },
            "tags": []
        }

    def to_update_note_fields_json(self, anki_id):
        return {
            "id": anki_id,
            "modelName": "Cloze with ID",
            "fields": {
                "ID": self.uuid,
                "Text": self.front,
            },
            "tags": []
        }


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


def extract_tags(regex: Pattern, line: str) -> Tuple[Optional[str], str]:
    match = re.match(regex, line)
    if not match:
        return None, line
    before, tag, after = match.groups()
    return tag, before + after


def make_anki_request(action, **params):
    request_json = json.dumps({'action': action, 'params': params, 'version': 6}).encode('utf-8')
    try:
        response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', request_json)))
    except urllib.error.URLError:
        raise ValueError("Anki must be running and AnkiConnect must be installed.")

    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def get_full_deck_name(full_deck_names: List[str], maybe_deck_name: Optional[str]) -> str:
    deck_name = maybe_deck_name or DEFAULT_DECK_NAME
    return next(x for x in full_deck_names if deck_name in x.lower())


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print(datetime.today(), "Building dashboard...")
        pages = {os.path.basename(x).rstrip('.md'): open(x, 'r').read() for x in glob.glob(Filepaths.BACKUP_DIR.value) if os.path.isfile(x)}
        graph = Graph()
        flashcards: List[AnkiFlashcard] = []
        full_deck_names = make_anki_request('deckNames')

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
                    well_formatted_flashcard = re.match(FLASHCARD_FRONT_REGEX, line)
                    if not well_formatted_flashcard:
                        print(f"Flashcard front improperly formatted: {line}")
                        continue

                    front_1, flashcard_uuid, front_2 = well_formatted_flashcard.groups()
                    front = front_1.strip() + " " + front_2.strip()

                    # Handle Cloze-style flashcards
                    is_cloze = re.search(CLOZE_REGEX, front)
                    if is_cloze:
                        front = re.sub(CLOZE_REGEX, lambda x: "{{c1::" + x.group(1) + "}}", front)
                        front = AnkiFlashcard.maybe_download_media_files_and_convert(front)

                        maybe_deck_name, line = extract_tags(ANKI_DECK_TAG_REGEX, line)
                        deck_name = get_full_deck_name(full_deck_names, maybe_deck_name)
                        flashcards.append(ClozeFlashcard(uuid=flashcard_uuid, front=front, deck=deck_name))
                        continue

                    is_num_lines_long_enough = i + 1 < num_bulleted_lines
                    if not is_num_lines_long_enough:
                        print(f"Flashcard is missing a back: {line}")
                        continue

                    # Handle two-sided flashcards
                    next_line = bulleted_lines[i + 1]
                    next_line_is_indented = re.match(BULLET_REGEX, line).span()[1] < re.match(BULLET_REGEX, next_line).span()[1]
                    if next_line_is_indented:
                        back = re.match(SANS_BULLET_REGEX, next_line).group(1).strip()
                        front = AnkiFlashcard.maybe_download_media_files_and_convert(front)
                        back = AnkiFlashcard.maybe_download_media_files_and_convert(back)

                        maybe_deck_name, line = extract_tags(ANKI_DECK_TAG_REGEX, line)
                        deck_name = get_full_deck_name(full_deck_names, maybe_deck_name)
                        flashcards.append(TwoSidedFlashcard(uuid=flashcard_uuid, front=front, back=back, deck=deck_name))

                        continue

                    print(f"Flashcard improperly formatted (next line not indented): {line}\n{next_line}")

        try:
            make_anki_request('sync')
        except Exception:
            print("Waiting on sync...")
            time.sleep(5)
            try:
                make_anki_request('sync')
            except Exception:
                print("Waiting on sync...")
                time.sleep(5)
                make_anki_request('sync')

        # POST flashcards to AnkiConnect
        for flashcard in flashcards:
            query = f"deck:{flashcard.deck} ID:{flashcard.uuid}"
            anki_ids = make_anki_request('findNotes', query=query)
            if len(anki_ids) == 0:
                make_anki_request('addNote', note=flashcard.to_add_note_json())
            elif len(anki_ids) == 1:
                make_anki_request('updateNoteFields', note=flashcard.to_update_note_fields_json(anki_ids[0]))
            else:
                raise AssertionError(f"{len(anki_ids)} number of cards returned for query {query}")

        make_anki_request('sync')

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
        with open(Filepaths.NUM_EDGES_FILEPATH.value, "r+") as f:
            line = f"\n{datetime.today()} {num_edges}"
            if line not in f.read():
                f.write(line)

        # Save word count
        with open(Filepaths.WORD_COUNT_FILEPATH.value, "r+") as f:
            line = f"\n{datetime.today()} {word_count}"
            if line not in f.read():
                f.write(line)

        # Save shares
        with open(Filepaths.NUM_SHARES_FILEPATH.value, "r+") as f:
            line = f"\n{datetime.today()} {num_shares}"
            if line not in f.read():
                f.write(line)

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
