#!/bin/sh
export CONFIG="$1"
export directory="$2"
gunicorn app:app -w 2 --threads 2 -b 0.0.0.0:3000