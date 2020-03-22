import re
from argparse import FileType
from datetime import datetime
from sys import stdin
from typing import List

import attr
from dateutil import parser
from dateutil.parser import ParserError
from django.core.management import BaseCommand
from jinja2 import Template

DATA_DIR = "Users/jasonbenn/data/Roam-Export-1584772783629"


@attr.s
class Note:
    title: str = attr.ib()
    dates: List[datetime] = attr.ib()
    tags: List[str] = attr.ib()

    @classmethod
    def from_line(cls, raw_line: str) -> "Note":
        line = raw_line.lstrip(DATA_DIR)
        note_title, note_str = line.split(':', 1)
        # Title might be a date, or the note title.
        title = note_title.rstrip(".md")
        tags = re.findall("(#[\w\d]+)", note_str)
        try:
            date = parser.parse(title)
            # If that worked, this is a one-line note fragment.
            title = note_str.lstrip("- ")
            dates = [date]
        except ParserError:
            dates = [parser.parse(x.lstrip('#')) for x in tags if any([str(y) in x for y in [2019, 2020, 2021]])]

        return cls(title, dates, tags)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('input', nargs='?', type=FileType('r'), default=stdin)

    def handle(self, *args, **kwargs):
        # Read the zip files' mtime, make a note of when this was last updated.

        # lines = [x for x in kwargs['input'].read().split('\n') if x]
        # notes = [Note.from_line(x) for x in lines]
        # print(notes[:3])

        template = Template(open('web/templates/dashboard.html').read())

        with open("build/index.html", "w") as f:
            f.write(template.render(test_value="allo", last_updated=datetime.today()))


# /Users/jasonbenn/data/Roam-Export-1584772783629/March 20th, 2020.md:- #Notes workaholism can make sense when you own the value of your work. burnouts and inconsistent motivation are much bigger problems when you are working for someone else's benefit.

# /Users/jasonbenn/data/Roam-Export-1584772783629/Intelligence is compression.md:- Tags:: #Notes #CS294 #AI

# /Users/jasonbenn/data/Roam-Export-1584772783629/Why Gradient Clipping Accelerates Training.md:Tags:: #[[ML papers]] #Notes [[March 10th, 2020]] [[March 11th, 2020]]

# /Users/jasonbenn/data/Roam-Export-1584772783629/AI research knowledge is organizational, not individual.md:- Tags:: #Tweets [[February 17th, 2020]] #Research #AI #[[Learning organizations]] [[Knowledge theory]] [[Organizational theory]] #Notes
