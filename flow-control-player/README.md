Control de flujo multimedia
---------------------------

Debido a la tasa de consumo del reproductor, el servidor adapta automáticamente la tasa de recepción al bitrate del fichero .mp3 que se envíe. Y como consecuencia también la adapta el cliente.

Ejecuta estos comandos en terminales diferentes.

Servidor:

    $ ./server.py 2000 | mpg123 --quiet -

Cliente:

    $ ./client.py localhost 2000 < song.mp3


El servidor genera un fichero stats.csv, que puedes procesar con `gnuplot rate.gp` para generar una gráfica.
