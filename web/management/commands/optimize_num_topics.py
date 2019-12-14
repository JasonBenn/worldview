import matplotlib.pyplot as plt
from tqdm import tqdm
from django.core.management import BaseCommand

from web.models import NotionDocument
from web.utils import make_topic_model
from web.utils import plot_and_show
from web.utils import preprocess_docs_to_words


class Command(BaseCommand):
    def handle(self, *args, **options):
        notion_docs = NotionDocument.objects.all()
        text_docs = [x.to_plaintext() for x in notion_docs]
        words = preprocess_docs_to_words(text_docs)
        coherence_scores = []
        min_num_topics = 4
        max_num_topics_inclusive = 40
        step_size = 4
        all_num_topics = list(range(min_num_topics, max_num_topics_inclusive + 1, step_size))
        print("Making LDA models and measuring coherence...")
        for num_topics in tqdm(all_num_topics):
            lda_model, coherence_score = make_topic_model(words, num_topics)
            coherence_scores.append(coherence_score)
        print(coherence_scores)

        plt.plot(all_num_topics, coherence_scores)
        plt.xlabel("Num Topics")
        plt.ylabel("Coherence score")
        plt.legend(("coherence_scores"), loc='best')
        plot_and_show("num_topics_to_lda_model_coherence")
