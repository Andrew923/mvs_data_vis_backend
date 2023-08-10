#!/bin/sh
# if [ $# -eq 2 ]; then
#   export directory="$2"
#   export CONFIG="$1"
# fi
# if [[ $# -eq 0 ]]; then
#   gunicorn app:app -w 2 --threads 2 -b 0.0.0.0:3000 --certfile certificate.crt --keyfile private.key --ca-certs ca_bundle.crt
# else
#   gunicorn mvs_data_vis_backend.app:app -w 2 --threads 2 -b 0.0.0.0:3000
# fi

#Tmux running both frontend and backend
tmux new-session -d -s app

tmux new-window -t app:1 -n "Gunicorn"
tmux send-keys -t app:1 "gunicorn mvs_data_vis_backend.app:app -w 2 --threads 2 -b 0.0.0.0:49153" C-m

tmux new-window -t app:2 -n "NPM"
tmux send-keys -t app:2 "npm start --prefix mvs_data_vis/" C-m
tmux a

# gunicorn mvs_data_vis_backend.app:app -w 2 --threads 2 -b 0.0.0.0:3001
# npm start --prefix mvs_data_vis/