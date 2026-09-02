#!/usr/bin/env python3
# Minimal web server that replies with the client's public IP.
#
#   $ curl http://localhost:8000
#   203.0.113.7

import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class WhatsMyIP(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (self.client_address[0] + '\n').encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Listening on port {port}...")
    HTTPServer(('', port), WhatsMyIP).serve_forever()
