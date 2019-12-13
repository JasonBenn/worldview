import json

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
    document_query = Document.objects.filter(embedding_type=EmbeddingType.LEMMATIZED_TF_IDF)
    unprojected_count = document_query.filter(embedding__isnull=True).count()
    if unprojected_count:
        print(f"Number of documents without projections: {unprojected_count}")

    docs = document_query.select_related('source__notiondocument')
    xs, ys, document_db_ids, texts = zip(*[(
        x.projection[0],
        x.projection[1],
        x.source.notiondocument.parent_database_id,
        x.text
    ) for x in docs])

    worldview_db_id = NotionDatabase.objects.get(title="Worldview").id

    context = {
        "xs": json.dumps(xs),
        "ys": json.dumps(ys),
        "texts": json.dumps([insert_linebreaks(x) for x in texts]),
        "colors": json.dumps(document_db_ids),
        "symbols": json.dumps([DONE_SYMBOL if x == worldview_db_id else INBOX_SYMBOL for x in document_db_ids]),
        "color_min": NotionDatabase.objects.order_by('id').first().id,
        "color_max": NotionDatabase.objects.order_by('id').last().id,
    }

    return render(request, 'index.html', context)
