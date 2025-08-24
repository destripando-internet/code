Flow control for media stream
-----------------------------

The server's receiving rate automatically adapts to the MP3 player's bitrate thanks to flow control.

run server:

```
$ ./server.py 2000 | mplayer -quiet -
```

run client:

```
$ ./client.py localhost 2000 < audio.mp3
```
