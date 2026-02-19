#!/bin/bash

tmux new-session -d -s session

tmux set-option -g mouse on
tmux setw -g monitor-activity on
tmux set-option -g visual-activity on
tmux bind-key x kill-session
tmux set-option -g set-titles off

tmux split-window -h
tmux send-keys -t session:0.0 './client.py --stdin --sndbuf 4000 127.0.0.1 2000 < song.mp3' C-m
tmux send-keys -t session:0.1 './server.py 2000 --stdout --rcvbuf 4000 | mpg123 -q -' C-m
tmux attach-session -t session
