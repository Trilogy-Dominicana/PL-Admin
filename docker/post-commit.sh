#!/bin/sh
# Update database with new data
docker container exec pl-admin pladmin wc2db -f

exit 0
