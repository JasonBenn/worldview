import json

from django.shortcuts import render

from web.models import Document
from web.models import NotionDatabase

INBOX_SYMBOL = 100
DONE_SYMBOL = 200


def index(request):
    unprojected_count = Document.objects.filter(embedding__isnull=True).count()
    if unprojected_count:
        print(f"Number of documents without projections: {unprojected_count}")
    Document.objects.values('projection', 'source__notiondocument__parent_database')
    xs, ys, document_db_ids, texts = zip(
        *[(x.projection[0], x.projection[1], x.source.notiondocument.parent_database_id, x.text) for x in
          Document.objects.all().select_related('source__notiondocument')])

    # db_ids = NotionDatabase.objects.values_list('id', flat=True).order_by('id')
    worldview_db_id = NotionDatabase.objects.get(title="Worldview").id
    # color_palette = sns.color_palette(n_colors=len(db_ids))
    # color_map = dict(zip(db_ids, color_palette))
    # colors = [color_map[x] for x in document_db_ids]

    context = {
        "xs": json.dumps(xs),
        "ys": json.dumps(ys),
        "texts": json.dumps(texts),
        "colors": json.dumps(document_db_ids),
        "symbols": json.dumps([DONE_SYMBOL if x == worldview_db_id else INBOX_SYMBOL for x in document_db_ids]),
        "color_min": NotionDatabase.objects.order_by('id').first().id,
        "color_max": NotionDatabase.objects.order_by('id').last().id,
    }

    return render(request, 'index.html', context)
