#!/bin/bash
set -e
LOGFILE=/var/log/gunicorn/django-bigpeople.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3 # 1 + 2 * NUM_CORES

USER=www-data
GROUP=www-data

cd /home/denis/bigpeople/
test -d $LOGDIR || mkdir -p $LOGDIR
exec gunicorn_django -w $NUM_WORKERS \
    --log-level=debug \
    --log-file=$LOGFILE 2>>$LOGFILE \
    --user=$USER --group=$GROUP