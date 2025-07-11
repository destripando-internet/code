#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <server-script> <client-script>"
    exit 1
fi

SERVER=$1
CLIENT=$2

tmux -f .tmux.conf new-session -d -s session
tmux -f .tmux.conf split-window -h
tmux -f .tmux.conf send-keys -t session:0.0 "./$SERVER 2000" C-m
tmux -f .tmux.conf send-keys -t session:0.1 "sleep 1; ./$CLIENT localhost 2000" C-m
tmux -f .tmux.conf attach-session -t session
