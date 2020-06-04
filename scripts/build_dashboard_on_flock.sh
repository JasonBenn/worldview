#!/usr/bin/env bash

WORLDVIEW_PATH=/home/flock/worldview
date > ${WORLDVIEW_PATH}/data/dashboard_built_at.txt
pushd /home/flock/roam-notes
git pull --quiet
popd

source /home/flock/venvs/worldview/bin/activate
python ${WORLDVIEW_PATH}/manage.py build_dashboard
