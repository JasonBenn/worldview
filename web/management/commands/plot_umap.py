import json
import os
import subprocess

import matplotlib.pyplot as plt
import seaborn as sns
from django.conf import settings
from django.core.management.base import BaseCommand

from web.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        unprojected_count = Document.objects.filter(embedding__isnull=True).count()
        if unprojected_count:
            print(f"Number of documents without projections: {unprojected_count}")
        Document.objects.values('projection', 'source__notiondocument__parent_database')
        xs, ys, document_db_ids, texts = zip(*[(x.projection[0], x.projection[1], x.source.notiondocument.parent_database_id, x.text) for x in Document.objects.all().select_related('source__notiondocument')])

        db_ids = NotionDatabase.objects.values_list('id', flat=True).order_by('id')
        color_palette = sns.color_palette(n_colors=len(db_ids))
        color_map = dict(zip(db_ids, color_palette))
        colors = [color_map[x] for x in document_db_ids]

        plt.scatter(xs, ys, c=colors)

        plt.gca().set_aspect('equal', 'datalim')
        plt.title('UMAP projection of Worldview', fontsize=24)

        # filename = f"nieghbors_{n_neighbors}__min_dist_{min_dist}"
        filename = f"test"
        dirpath = f"{settings.BASE_DOCUMENT_DIR}/umaps"
        os.makedirs(dirpath, exist_ok=True)
        filepath = f"{dirpath}/{filename}.png"
        plt.savefig(filepath)
        subprocess.call(["open", filepath])

        points_filepath = f"{dirpath}/{filename}.json"

        points = {
            "x": xs,
            "y": ys,
            "mode": 'markers',
            "type": 'scatter',
            "text": texts,
            "textfont": {
                "family": 'Times New Roman'
            },
            "marker": {"color": colors},
            "hoverinfo": "text"
        }

        open(points_filepath, 'w').write(json.dumps(points))
