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

    tmux  send-keys -t session:0.0 "docker run --rm --name mosquitto -p 1883:1883 eclipse-mosquitto mosquitto -c /mosquitto-no-auth.conf" C-m
    tmux  send-keys -t session:0.1 "sleep 1; ./chatroom-member.py localhost Alice" C-m
    tmux  send-keys -t session:0.2 "sleep 1; ./chatroom-member.py localhost Bob" C-m
    tmux  send-keys -t session:0.3 "sleep 1; ./chatroom-member.py localhost Charlie" C-m

    tmux  attach-session -t session
)
