import http.server
import json
import socketserver
from modules.database import Database
from modules import ServerEvents as Events

class MessageServerHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(403, "Directory listing not allowed")
        return None
    
    def do_POST(self):
        if self.path == '/createUserAccount':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                name = data.get('name')
                passwdhash = data.get('passwdhash')
                
                if name and passwdhash:
                    success, message = Events.create_account(name, passwdhash, Database.FreecordDB)
                    if not success:
                        self.send_error(400, message)
                        return

                    self.send_response(200, message)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "account created"}')
                else:
                    self.send_error(400, "Missing name or password")
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
            except Exception as e:
                self.send_error(400, e)
        elif self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body.decode('utf-8'))
                name = data.get('name')
                passwdhash = data.get('passwdhash')

                if name and passwdhash:
                    user_list = Database.FreecordDB().select("users", {"name": name})
                    
                    if not user_list:
                        self.send_error(404, "User doesn't exist")
                        return

                    user = user_list[0]
                    if user['passwdhash'] == passwdhash:
                        response_data = {
                            "status": "success",
                            "message": "Logged in successfully",
                            "user_token": user['user_token']
                        }
                        response_bytes = json.dumps(response_data).encode('utf-8')

                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Content-Length', len(response_bytes))
                        self.end_headers()
                        self.wfile.write(response_bytes)
                    else:
                        self.send_error(401, "Invalid password")
                else:
                    self.send_error(400, "Missing name or password")

            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
            except Exception as e:
                self.send_error(500, str(e))
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