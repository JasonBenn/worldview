import json
from collections import defaultdict

from django.shortcuts import render

from web.models import Document
from web.models import EmbeddingType
from web.models import NotionDatabase

INBOX_SYMBOL = 100
DONE_SYMBOL = 200


def insert_linebreaks(text: str, window_size: int = 80) -> str:
    lines = text.split("\n")
    split_lines = []
    for line in lines:
        for i in range(0, len(line) // window_size + 1):
            start_index = i * window_size
            end_index = start_index + window_size
            split_lines.append(line[start_index:end_index])
    return "<br>".join(split_lines)


def index(request):
    worldview_db = NotionDatabase.objects.get(title="Worldview")
    traces = []
    for db in NotionDatabase.objects.all():
        docs = Document.objects.filter(
            source__notiondocument__parent_database=db,
            embedding_type=EmbeddingType.LEMMATIZED_TF_IDF
        )

        xs, ys, texts = zip(*[(
            x.projection[0],
            x.projection[1],
            x.text
        ) for x in docs])

        traces.append({
            "name": db.title,
            "x": xs,
            "y": ys,
            "text": [insert_linebreaks(x) for x in texts],
            "mode": "markers",
            "type": "scatter",
            "hoverinfo": "text",
            "textfont": {"family": "Times New Roman"},
            "marker": {
                "symbol": [DONE_SYMBOL if db == worldview_db else INBOX_SYMBOL] * len(docs)
            }
        })

    return render(request, 'index.html', {"data": json.dumps(traces)})
