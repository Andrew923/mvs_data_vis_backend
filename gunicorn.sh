#!/bin/sh
if [ $# -eq 2 ]; then
  export CONFIG="$1"
  export directory="$2"
fi
gunicorn app:app -w 2 --threads 2 -b 0.0.0.0:3000 --certfile certificate.crt --keyfile private.key --ca-certs ca_bundle.crt