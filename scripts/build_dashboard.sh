#!/usr/bin/env bash

BUCKET=jbenn-roam-backups
KEY=`aws --profile jason s3 ls ${BUCKET}/backups --recursive | sort | tail -n 1 | awk '{print $4}'`
aws --profile jason s3 cp s3://${BUCKET}/${KEY} data/roam-backup.zip
unzip data/roam-backup.zip -d data/roam-backup
./manage.py build_dashboard