import pickle
from pathlib import Path

from goodreads import gr_client
from goodreads import gr_client
from goodreads import gr_client
from goodreads import gr_client
from web.services.goodreads_service.types import GoodReadsEntityType
from web.services.goodreads_service.types import GoodReadsEntityType
from web.services.goodreads_service.types import GoodReadsEntityType
from web.services.goodreads_service.types import GoodReadsEntityType
from web.services.goodreads_service.types import GoodReadsEntityType


def load_entity(entity_type: GoodReadsEntityType, gr_id: str):
    dir_path = Path('data/goodreads_api').absolute()
    filepath = dir_path / entity_type.to_path() / gr_id
    if filepath.exists():
        return pickle.load(open(filepath, 'rb'))
    else:
        if entity_type == GoodReadsEntityType.BOOK:
            entity = gr_client.Book.show(gr_id)
        elif entity_type == GoodReadsEntityType.AUTHOR:
            entity = gr_client.Author.show(gr_id)
        elif entity_type == GoodReadsEntityType.SERIES:
            entity = gr_client.Series.show(gr_id)
        elif entity_type == GoodReadsEntityType.SHELVES:
            # Shelves only make sense to list by user_id, as they don't have known IDs.
            entity = gr_client.Shelf.list(gr_id)
        else:
            raise Exception
        pickle.dump(entity, open(filepath, 'wb'))
        return entity
