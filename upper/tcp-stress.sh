#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <server-script> <n_clients>"
    exit 1
fi

SERVER=$1
N_CLIENTS=$2

tmux new-session -d -s session

tmux set-option -g mouse on
tmux setw -g monitor-activity on
tmux set-option -g visual-activity on
tmux bind-key x kill-session
tmux set-option -g set-titles off

tmux split-window -h
tmux send-keys -t session:0.0 "./$SERVER 2000" C-m
tmux send-keys -t session:0.1 "sleep 1; ./tcp_stress_client.py 127.0.0.1 2000 $2" C-m
tmux attach-session -t session
