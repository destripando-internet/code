#!/bin/bash
shopt -s expand_aliases


tmux new-session -d -s session

tmux set-option -g mouse on
tmux setw -g monitor-activity on
tmux set-option -g visual-activity on
tmux bind-key x kill-session
tmux set-option -g set-titles off

tmux send-keys 'clear; echo "==== Puedes cerrar esta ventana con Ctrl-b x ===="; bash' C-m
tmux split-window -h
tmux send-keys -t session:0.0 "iperf -s -u -B 239.1.1.1" C-m
tmux send-keys -t session:0.1 "docker exec node3 iperf -s -u -B 239.1.1.1" C-m
tmux split-window -v
tmux send-keys -t session:0.2 "docker exec node2 iperf -c 239.1.1.1 -u -t 5 -T 64" C-m
tmux attach-session -t session
