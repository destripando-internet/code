#!/usr/bin/env python3
# Copyright: See AUTHORS and COPYING

import json
import sys
import paho.mqtt.client as mqtt

TOPIC = 'chatroom'
QUIT  = 'bye'


class ChatroomMember:
    def __init__(self, broker, nick):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(*broker)
        self.nick = nick

    def on_connect(self, client, userdata, flags, reason_code, properties):
        self.client.subscribe(TOPIC)

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        if data['nick'] == self.nick:
            return

        print("{}: {}".format(data['nick'], data['message']))

    def run(self):
        self.client.loop_start()

        while True:
            line = input()
            if line == QUIT:
                break

            payload = json.dumps({'nick': self.nick, 'message': line})
            self.client.publish(TOPIC, payload)

        self.client.loop_stop()
        self.client.disconnect()


if len(sys.argv) != 3:
    exit("Usage: ./chatroom-member.py <broker_address> <nick>")

broker = (sys.argv[1], 1883)

try:
    ChatroomMember(broker, nick=sys.argv[2]).run()
except (KeyboardInterrupt, EOFError):
    print("shut down.")
