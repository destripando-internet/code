#!/bin/bash

(
    unalias -a
    unset -f $(compgen -A function)
    export PS1='$ '

    set -g mouse on
    setw -g monitor-activity on
    set -g visual-activity on
    bind-key x kill-session
    set-option -g set-titles off

    tmux  new-session -d -s session
    tmux  split-window -h -t session:0

    tmux  split-window -v -t session:0.1
    tmux  split-window -v -t session:0.2

    tmux  send-keys -t session:0.0 "./chatroom-broker.py" C-m
    tmux  send-keys -t session:0.1 "sleep 1; ./chatroom-member.py" C-m
    tmux  send-keys -t session:0.2 "sleep 1; ./chatroom-member.py" C-m
    tmux  send-keys -t session:0.3 "sleep 1; ./chatroom-member.py" C-m

    tmux  attach-session -t session
)
