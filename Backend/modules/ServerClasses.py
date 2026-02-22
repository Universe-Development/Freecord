import http.server
import json
import socketserver
from modules.database import Database
from modules import ServerEvents as Events

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

class MessageServerHandler(http.server.SimpleHTTPRequestHandler):
    db: Database.FreecordDB | None = None

    def list_directory(self, path):
        self.send_error(403, "Directory listing not allowed")
        return None

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))

    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_POST(self):
        if self.db is None:
            self.send_error(500, "Database not initialized")
            return
        try:
            if self.path == '/createUserAccount':
                data = self._read_json_body()
                name = data.get('name')
                passwdhash = data.get('passwdhash')

                if not name or not passwdhash:
                    self.send_error(400, "Missing name or password")
                    return

                success, message = Events.create_account(name, passwdhash, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"status": "account created"})

            elif self.path == '/login':
                data = self._read_json_body()
                name = data.get('name')
                passwdhash = data.get('passwdhash')

                if not name or not passwdhash:
                    self.send_error(400, "Missing name or password")
                    return

                user_list = self.db.select("users", {"username": name})
                if not user_list:
                    self.send_error(404, "User doesn't exist")
                    return

                user = user_list[0]
                if user['hashed_passwd'] != passwdhash:
                    self.send_error(401, "Invalid password")
                    return

                self._send_json(200, {
                    "status": "success",
                    "message": "Logged in successfully",
                    "user_token": user['user_token']
                })

            elif self.path == '/createServer':
                data = self._read_json_body()
                name = data.get('name')
                user_token = data.get('user_token')

                if not name or not user_token:
                    self.send_error(400, "Missing name or user_token")
                    return

                success, message, result = Events.create_server(name, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "server created",
                    "server_id": result['server_id']
                })

            elif self.path == '/createChannel':
                data = self._read_json_body()
                name = data.get('name')
                server_id = data.get('server_id')
                user_token = data.get('user_token')
                channel_type = data.get('channel_type', 'text')

                if not name or not server_id or not user_token:
                    self.send_error(400, "Missing name, server_id, or user_token")
                    return

                if channel_type not in ('text', 'voice'):
                    self.send_error(400, "channel_type must be 'text' or 'voice'")
                    return

                try:
                    server_id = int(server_id)
                except (ValueError, TypeError):
                    self.send_error(400, "server_id must be an integer")
                    return

                success, message, result = Events.create_channel(name, server_id, user_token, self.db, channel_type)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "channel created",
                    "channel_id": result['channel_id']
                })

            else:
                self.send_error(404, "Not found")

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, str(e))


class MessageServer:
    def __init__(self):
        self.httpd = None

    def start(self, port: int, db: Database.FreecordDB):
        MessageServerHandler.db = db
        self.httpd = ThreadedTCPServer(("0.0.0.0", port), MessageServerHandler)
        self.httpd.serve_forever()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
