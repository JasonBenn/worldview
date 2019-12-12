import json

import seaborn as sns
from django.shortcuts import render

from web.models import Document
from web.models import NotionDatabase


def index(request):
    unprojected_count = Document.objects.filter(embedding__isnull=True).count()
    if unprojected_count:
        print(f"Number of documents without projections: {unprojected_count}")
    Document.objects.values('projection', 'source__notiondocument__parent_database')
    xs, ys, document_db_ids, texts = zip(
        *[(x.projection[0], x.projection[1], x.source.notiondocument.parent_database_id, x.text) for x in
          Document.objects.all().select_related('source__notiondocument')])

    db_ids = NotionDatabase.objects.values_list('id', flat=True).order_by('id')
    color_palette = sns.color_palette(n_colors=len(db_ids))
    color_map = dict(zip(db_ids, color_palette))
    colors = [color_map[x] for x in document_db_ids]

    context = {
        "xs": json.dumps(xs),
        "ys": json.dumps(ys),
        "texts": json.dumps(texts),
        "colors": json.dumps(colors)
    }
    return render(request, 'index.html', context)
