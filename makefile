SHELL := /usr/bin/env bash

# Commands API: Notion to Anki
export_worldview:
	python export_to_anki.py text https://www.notion.so/jasonbenn/d7a04baa1cea4dda983747b04ae3ddaa?v=727ed26317ec44caa4c9f2d8393a09b5

export_people:
	python export_to_anki.py people https://www.notion.so/jasonbenn/2f61537471d64420b40c263ea48ba9e8?v=823167eafe964ed096c24c0a038f5d2c

export_thinks:
	python export_to_anki.py text https://www.notion.so/jasonbenn/17213f11f7ef4814b06fe4966f446b91?v=7fee0e1edeb641f3adaebcf2d2e6d31d

export_all:
	make -j 3 export_thinks export_people export_worldview

# Commands API: UMAP
export_documents:
	python export_to_anki.py document https://www.notion.so/jasonbenn/d7a04baa1cea4dda983747b04ae3ddaa?v=727ed26317ec44caa4c9f2d8393a09b5

vectorize_documents:
	python vectorize.py

plot_umap:
	python plot_umap.py

# Utility
copy_umap_json:
	cat ~/.notion-to-anki/umaps/nieghbors_10__min_dist_0.5.json | pbcopy

# DB
init_postgres:
	createuser -s -P notion_to_anki
	createdb -W -h 127.0.0.1 notion_to_anki -U notion_to_anki -p 5432

psql:
	psql postgresql://notion_to_anki:notion_to_anki@127.0.0.1:5432/notion_to_anki

migrate:
	web/manage.py migrate
