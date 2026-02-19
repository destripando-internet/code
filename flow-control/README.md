Probando el control de flujo de TCP
-----------------------------------

El programa `client.py` es un emisor puro y el programa `server.py` es un receptor. El cliente mide la tasa de envío y el servidor la de recepción.

El servidor puede limitar artificialmente la tasa de recepción (opción --limit) y es posible  comprobar cómo eso afecta al cliente. El cliente envía tan rápido como puede.

Ejecuta estos comando en terminales diferentes.

Servidor:

    $ ./server.py --limit 200 2000

Cliente:

    $ ./client.py 127.0.0.1 2000

En el comando del servidor, el 2000 es el puerto de escucha y 200 es la tasa límite en kB/s.

Puedes comprobar que el cliente para el envío cuando los buffers de envío y recepción se llenan y reanuda cuando queda espacio libre (cuando el receptor abre la ventana).

Puedes generar gráficas con los datos enviados y la tasa de envío a partir del fichero `client-stats.csv` generado por el cliente:

    $ gnuplot client-sent.gp
    $ gnuplot client-rate.gp

Y puedes ver información sobre el socket con:

    $ ss -timon sport = 2000 or dport = 2000


Reproductor multimedia
----------------------

Por defecto el cliente solo envía datos de relleno, pero es posible indicarle que lea datos desde su entrada estándar con la opción `--stdin`. Por su parte el servidor descarta lo que recibe, pero también es posible indicar que envíe los datos a su salida estándar con `--stdout`. Este te permite usar esta conexión para enviar un flujo multimedia.

La entrada del cliente se puede redirigir desde un fichero .mp3, mientras que la salida del servidor se puede enviar a un reproductor. Con ello, la tasa de recepción se adapta automáticamente al bitrate del fichero mp3 que estés enviando, lo que a su vez limita la tasa de envío del cliente. Utiliza estos comandos:


Servidor:

    $ ./server.py --stdout --rcvbuf 4000 2000 | mpg123 --quiet -

Cliente:

    $ ./client.py  --stdin --sndbuf 4000 127.0.0.1 2000 < song.mp3


Las opciones --rcvbuf y --sndbuf fijan los tamaños de los buffers de recepción y envío de servidor y cliente.

El servidor genera un fichero `server-stats.csv`, que puedes procesar con `gnuplot server-rate.gp` para generar una gráfica.
