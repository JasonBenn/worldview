import json
import os
import pickle
import subprocess

import seaborn as sns
import matplotlib.pyplot as plt
from umap import UMAP

n_neighbors = 10
min_dist = 0.5
reducer = UMAP(n_neighbors=n_neighbors, min_dist=min_dist)
BASE_DIR = '/Users/jasonbenn/.notion-to-anki'
df = pickle.load(open(f'{BASE_DIR}/outputs/df.pkl', 'rb'))
vectors = list(df.vector.values)
documents = list(df.document.unique())
color_palette = sns.color_palette(n_colors=len(documents))
color_map = dict(zip(documents, color_palette))
colors = [color_map[x] for x in df.document.values]

embedding = reducer.fit_transform(vectors)

plt.scatter(embedding[:, 0], embedding[:, 1], c=colors)

plt.gca().set_aspect('equal', 'datalim')
plt.title('UMAP projection of Worldview', fontsize=24)

filename = f"nieghbors_{n_neighbors}__min_dist_{min_dist}"
dirpath = f"{BASE_DIR}/umaps"
os.makedirs(dirpath, exist_ok=True)
filepath = f"{dirpath}/{filename}.png"
plt.savefig(filepath)
subprocess.call(["open", filepath])

points_filepath = f"{dirpath}/{filename}.json"

xs, ys = zip(*embedding.tolist())
points = {
    "x": xs,
    "y": ys,
    "mode": 'markers',
    "type": 'scatter',
    "text": list(df.sentence.values),
    "textfont": {
        "family": 'Times New Roman'
    },
    "marker": {"color": colors},
    "hoverinfo": "text"
}

open(points_filepath, 'w').write(json.dumps(points))
