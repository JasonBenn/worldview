import json

from django.db.models import F
from django.shortcuts import render

from web.models import Document
from web.models import EmbeddingType
from web.models import NotionDatabase
from web.utils import normalized_notion_url

INBOX_SYMBOL = 100
DONE_SYMBOL = 200


def index(request):
    docs = list(Document.objects.filter(embedding_type=EmbeddingType.LEMMATIZED_TF_IDF).values('id', 'projection', 'text', 'source__notiondocument__json__page__properties', db_id=F('source__notiondocument__parent_database'), notion_id=F('source__notiondocument__notion_id')))

    db_id_to_titles = {x.id: x.title for x in NotionDatabase.objects.all()}

    for doc in docs:
        if db_id_to_titles[doc['db_id']] == "Worldview":
            doc['url'] = normalized_notion_url(doc['notion_id'])

    return render(request, 'index.html', {
        "graph": json.dumps(docs),
        "db_titles": db_id_to_titles,
        "recent_documents": Document.objects.filter(embedding_type=EmbeddingType.LEMMATIZED_TF_IDF)[:15].select_related('source__notiondocument')
    })
