SHELL := /usr/bin/env bash


export_worldview:
	python export.py text https://www.notion.so/jasonbenn/d7a04baa1cea4dda983747b04ae3ddaa?v=727ed26317ec44caa4c9f2d8393a09b5

export_people:
	python export.py people https://www.notion.so/jasonbenn/2f61537471d64420b40c263ea48ba9e8?v=823167eafe964ed096c24c0a038f5d2c

export_thinks:
	python export.py text https://www.notion.so/jasonbenn/17213f11f7ef4814b06fe4966f446b91?v=7fee0e1edeb641f3adaebcf2d2e6d31d

export_all:
	make -j 3 export_thinks export_people export_worldview