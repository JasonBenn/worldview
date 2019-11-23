import json
from pathlib import Path
from typing import Dict, List

import requests


# https://foosoft.net/projects/anki-connect/

storage_dir = Path("/Users/jasonbenn/.notion-to-anki")
filepaths = [x for x in storage_dir.glob("*") if x.is_file()]
filepath = filepaths[0]
filename = filepath.name
filenames = [x.name for x in filepaths]

doc_raw = open(str(filepath)).read()
doc_lines = [x for x in doc_raw.split("\n") if x]
doc_records = [dict(zip(("id", "front", "back"), x.split(';'))) for x in doc_lines]
ids_to_doc_records = {x["id"]: x for x in doc_records}
print(doc_records)

print("loading from", filepath)


def sync():
    post_anki_connect({
        "action": "sync",
        "version": 6
    })


def post_anki_connect(data):
    return requests.post("http://localhost:8765", json.dumps(data)).json()['result']


all_decks_to_ids = post_anki_connect({
    "action": "deckNamesAndIds",
    "version": 6
})

decks_to_ids = {deck_name: deck_id for deck_name, deck_id in all_decks_to_ids.items() if deck_name in filenames}
deck_name, deck_id = [x for x in decks_to_ids.items() if x[0] == filename][0]

note_ids = post_anki_connect({
    "action": "findNotes",
    "version": 6,
    "params": {
        "query": f"deck:{deck_name}"
    }
})


def get_notes_info(note_ids: List[int]) -> Dict:
    return post_anki_connect({
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    })


anki_notes = get_notes_info(note_ids)
anki_note = anki_notes[0]

ids_to_anki_notes = {x['fields']['ID']['value']: x for x in anki_notes}

to_update = set(ids_to_anki_notes) & set(ids_to_doc_records)
to_delete = set(ids_to_anki_notes) - set(ids_to_doc_records)
to_create = set(ids_to_doc_records) - set(ids_to_anki_notes)
print(f"update: {len(to_update)}, delete: {len(to_delete)}, create: {len(to_create)}")

doc_id = list(to_update)[0]

# for doc_id in to_update:
anki_id = ids_to_anki_notes[doc_id]['noteId']
print("before", get_notes_info([anki_id]))

front = ids_to_doc_records[doc_id]['front']
back = ids_to_doc_records[doc_id]['back']
result = post_anki_connect({
    "action": "updateNoteFields",
    "version": 6,
    "params": {
        "note": {
            "id": anki_id,
            "fields": {
                "Front": front,
                "Back": back
            }
        }
    }
})
print("after", get_notes_info([anki_id]))

print(f'deleting {to_delete}')
post_anki_connect({
    "action": "deleteNotes",
    "version": 6,
    "params": {
        "notes": list(to_delete)
    }
})

# addNote
add_note_data = {
    "action": "addNotes",
    "version": 6,
    "params": {
        "notes": [
            {
                "deckName": "Default",
                "modelName": "Basic",
                "fields": {
                    "Front": "front content",
                    "Back": "back content"
                },
                "tags": [
                    "yomichan"
                ],
                "audio": {
                    "url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji=猫&kana=ねこ",
                    "filename": "yomichan_ねこ_猫.mp3",
                    "skipHash": "7e2c2f954ef6051373ba916f000168dc",
                    "fields": [
                        "Front"
                    ]
                }
            }
        ]
    }
}
