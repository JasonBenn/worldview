from enum import Enum


class GoodReadsEntityType(Enum):
    BOOK = "BOOK"
    AUTHOR = "AUTHOR"
    SERIES = "SERIES"
    SHELVES = "SHELVES"

    def to_path(self):
        return self.value.lower()
