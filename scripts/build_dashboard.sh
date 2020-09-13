#!/usr/bin/env bash

WORLDVIEW_PATH=/Users/jasonbenn/code/worldview
BUCKET=jbenn-roam-backups/backups/
KEY=`aws --profile jason s3 ls ${BUCKET} | sort | tail -n 1 | awk '{print $4}'`
pushd ${WORLDVIEW_PATH}

aws --profile jason s3 cp s3://${BUCKET}${KEY} ./data/roam-backup.zip
rm ./data/roam-backup/*
unzip -o ./data/roam-backup.zip -d ./data/roam-backup
date > ./data/dashboard_built_at.txt
/Users/jasonbenn/.pyenv/versions/3.7.4/envs/worldview/bin/python ./manage.py build_dashboard
