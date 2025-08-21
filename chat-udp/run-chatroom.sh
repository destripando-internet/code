#!/bin/bash

(
    unalias -a
    unset -f $(compgen -A function)
    export PS1='$ '

    tmux -f .tmux.conf new-session -d -s session
    tmux -f .tmux.conf split-window -h -t session:0

    tmux -f .tmux.conf split-window -v -t session:0.1
    tmux -f .tmux.conf split-window -v -t session:0.2

    tmux -f .tmux.conf send-keys -t session:0.0 "./chatroom-broker.py" C-m
    tmux -f .tmux.conf send-keys -t session:0.1 "sleep 1; ./chatroom-member.py" C-m
    tmux -f .tmux.conf send-keys -t session:0.2 "sleep 1; ./chatroom-member.py" C-m
    tmux -f .tmux.conf send-keys -t session:0.3 "sleep 1; ./chatroom-member.py" C-m

    tmux -f .tmux.conf attach-session -t session
)
