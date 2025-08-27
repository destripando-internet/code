Control de flujo multimedia
---------------------------

El servidor adapta automáticamente la tasa de recepción el bitrate que corresponda al fichero .mp3 que se envíe, debido a la tasa de consumo del reproductor.

Ejecuta estos comandos en terminales diferentes.

Servidor:

    $ ./server.py 2000 | mpg123 --quiet -

Cliente:

    $ ./client.py localhost 2000 < song.mp3


El servidor genera un fichero stats.csv, que puedes procesar con `gnuplot rate.gp` para generar una gráfica.
