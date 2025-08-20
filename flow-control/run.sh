#!/bin/bash

tmux -f .tmux.conf new-session -d -s session
tmux -f .tmux.conf split-window -h
tmux -f .tmux.conf send-keys -t session:0.0 "sleep 1; ./client.py 127.0.0.1 2000" C-m
tmux -f .tmux.conf send-keys -t session:0.1 "./server.py 2000 200" C-m
tmux -f .tmux.conf attach-session -t session
