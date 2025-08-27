Probando el control de flujo de TCP
-----------------------------------

- `server.py` es un receptor que limita la tasa de llegada.
- `client.py` envía tan rápido como puede.
- `lazy-server.py` espera a que el usuario pulse una tecla antes de enviar algunos datos, después vuelve a pasar.

Ejecuta estos comando en terminales diferentes.

Servidor:

    $ ./server.py 2000 200

Cliente:

    $ ./client.py 127.0.0.1 2000

En el comando del servidor, el 2000 es el puerto de escucha y 200 es la tasa límite en kB/s.

Puedes comprobar que el cliente para el envío cuando lo buffer de envío y recepción se llenan y reanuda cuando queda espacio libre.

Puedes generar gráficas con los datos enviados y la tasa de envío a partir del fichero .csv generado por el cliente:

    $ gnuplot sent.gp
    $ gnuplot rate.gp

Puedes ver información sobre el socket con:

    $ ss -timon sport = 2000 or dport = 2000
