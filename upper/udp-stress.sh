#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <server-script> <n_clients>"
    exit 1
fi

SERVER=$1
N_CLIENTS=$2

tmux -f .tmux.conf new-session -d -s session
tmux -f .tmux.conf split-window -h
tmux -f .tmux.conf send-keys -t session:0.0 "./$SERVER 2000" C-m
tmux -f .tmux.conf send-keys -t session:0.1 "sleep 1; ./udp_stress_client.py 127.0.0.1 2000 $2" C-m
tmux -f .tmux.conf attach-session -t session
