import http.server
import socketserver

class MessageServerHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(403, "Directory listing not allowed")
        return None
    
    def do_POST(self):
        if self.path == '/getUserInfo': # TODO: Actually implement the fucking logic
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
        else:
            self.send_error(404, "Not found")

class MessageServer:
    def __init__(self):
        self.httpd = None

    def start(self, port=9042):
        self.httpd = socketserver.TCPServer(("0.0.0.0", port), MessageServerHandler)
        self.httpd.serve_forever()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()