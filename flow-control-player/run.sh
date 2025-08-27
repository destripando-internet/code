#!/bin/bash

tmux -f .tmux.conf new-session -d -s session
tmux -f .tmux.conf split-window -h
tmux -f .tmux.conf send-keys -t session:0.0 'sleep 1; ./client.py localhost 2000 < song.mp3' C-m
tmux -f .tmux.conf send-keys -t session:0.1 './server.py 2000 | mpg123 -q -' C-m
tmux -f .tmux.conf attach-session -t session
