#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <server-script> <client-script>"
    exit 1
fi

SERVER=$1
CLIENT=$2

tmux new-session -d -s session

tmux set-option -g mouse on
tmux setw -g monitor-activity on
tmux set-option -g visual-activity on
tmux bind-key x kill-session
tmux set-option -g set-titles off

tmux split-window -h
tmux send-keys -t session:0.0 "./$SERVER 2000 --limit 200" C-m
tmux send-keys -t session:0.1 "sleep 1; ./$CLIENT 127.0.0.1 2000" C-m
tmux attach-session -t session
