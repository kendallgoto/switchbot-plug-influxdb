#!/bin/sh

rc-status

rc-service dbus start
rc-service bluetooth start

python ./app.py
