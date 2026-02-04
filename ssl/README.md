## SSL

* [server][ssl-server]
* [client][ssl-client]

[ssl-server]: https://github.com/destripando-internet/code/blob/master/ssl/server.py
[ssl-client]: https://github.com/destripando-internet/code/blob/master/ssl/client.py

### SSL certs

Generate CA (Certification Authority):

    $ openssl req -x509 -newkey rsa:4096 -keyout ca-key.pem -out ca-cert.pem -nodes -subj "/CN=MyCA"

* ca-key.pem: CA private key
* ca-cert.pem: CA certificate

Generate server private key:

    $ openssl req -newkey rsa:4096 -keyout server-key.pem -out server-req.pem -nodes -subj "/CN=localhost"

* server-key.pem: private server key
* server-req.pem: sign request for CA

Sign server cert with CA:

    $ openssl x509 -req -in server-req.pem -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem

* server-cert.pem: signed server certificate
