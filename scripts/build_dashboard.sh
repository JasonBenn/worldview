#!/usr/bin/env bash

WORLDVIEW_PATH=/Users/jasonbenn/code/worldview
BUCKET=jbenn-roam-backups/backups/
KEY=`aws --profile jason s3 ls ${BUCKET} | sort | tail -n 1 | awk '{print $4}'`
aws --profile jason s3 cp s3://${BUCKET}${KEY} ${WORLDVIEW_PATH}/data/roam-backup.zip
rm ${WORLDVIEW_PATH}/data/roam-backup/*
unzip -o ${WORLDVIEW_PATH}/data/roam-backup.zip -d ${WORLDVIEW_PATH}/data/roam-backup
date > ${WORLDVIEW_PATH}/data/dashboard_built_at.txt
/Users/jasonbenn/.pyenv/versions/3.7.4/envs/worldview/bin/python ${WORLDVIEW_PATH}/manage.py build_dashboard
