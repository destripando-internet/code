#!/bin/bash

tmux new-session -d -s session

tmux set-option -g mouse on
tmux setw -g monitor-activity on
tmux set-option -g visual-activity on
tmux bind-key x kill-session
tmux set-option -g set-titles off

tmux split-window -h
tmux send-keys -t session:0.0 "./client.py 127.0.0.1 2000" C-m
tmux send-keys -t session:0.1 "./server.py 2000 --limit 200" C-m
tmux split-window -v -l 2
tmux send-keys -t session:0.2 "sleep 70; tmux kill-session -t session" C-m
tmux attach-session -t session
