#!/bin/sh
# If the /data volume is mounted onto the container, the volume is owned by the host and is inaccessible to the container.
# The purpose of this entrypoint is to chown the host directory to something the container can access and update. 
set -e
mkdir -p /app/data
chown -R app:app /app/data
exec gosu app "$@"