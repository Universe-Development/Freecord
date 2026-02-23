import http.server
import json
import socketserver
from urllib.parse import urlparse, parse_qs
from modules.database import Database
from modules import ServerEvents as Events

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class MessageServerHandler(http.server.SimpleHTTPRequestHandler):
    db: Database.FreecordDB | None = None

    def log_message(self, format, *args):
        pass

    def list_directory(self, path):
        self.send_error(403, "Directory listing not allowed")
        return None

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))

    def _send_json(self, status_code: int, data: dict | list):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _get_auth_token(self) -> str | None:
        auth = self.headers.get('Authorization', '').strip()
        return auth if auth else None

    def _db_guard(self) -> bool:
        if self.db is None:
            self.send_error(500, "Database not initialized")
            return False
        return True

    def _require_auth(self) -> str | None:
        token = self._get_auth_token()
        if not token:
            self.send_error(401, "Missing Authorization header")
            return None
        return token

    def do_POST(self):
        if not self._db_guard():
            return
        assert self.db is not None
        try:
            parsed_path = urlparse(self.path).path

            if parsed_path == '/createUserAccount':
                data = self._read_json_body()
                name = data.get('name')
                passwdhash = data.get('passwdhash')

                if not name or not passwdhash:
                    self.send_error(400, "Missing name or passwdhash")
                    return

                success, message = Events.create_account(name, passwdhash, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"status": "account created"})

            elif parsed_path == '/login':
                data = self._read_json_body()
                name = data.get('name')
                passwdhash = data.get('passwdhash')

                if not name or not passwdhash:
                    self.send_error(400, "Missing name or passwdhash")
                    return

                user_list = self.db.select("users", {"username": name})
                if not user_list:
                    self.send_error(404, "User not found")
                    return

                user = user_list[0]
                if user['hashed_passwd'] != passwdhash:
                    self.send_error(401, "Invalid password")
                    return

                self._send_json(200, {
                    "status": "success",
                    "message": "Logged in successfully",
                    "user_token": user['user_token'],
                    "user_id": user['user_id'],
                })

            elif parsed_path == '/createServer':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                name = data.get('name')

                if not name:
                    self.send_error(400, "Missing server name")
                    return

                success, message, result = Events.create_server(name, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "server created",
                    "server_id": result['server_id'],
                })

            elif parsed_path == '/createChannel':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                name = data.get('name')
                server_id = data.get('server_id')
                channel_type = data.get('channel_type', 'text')

                if not name or not server_id:
                    self.send_error(400, "Missing name or server_id")
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
                    "channel_id": result['channel_id'],
                })

            elif parsed_path == '/createInvite':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                server_id = data.get('server_id')

                if not server_id:
                    self.send_error(400, "Missing server_id")
                    return

                try:
                    server_id = int(server_id)
                except (ValueError, TypeError):
                    self.send_error(400, "server_id must be an integer")
                    return

                success, message, result = Events.create_invite(server_id, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "invite created",
                    "invite_code": result['invite_code'],
                })

            elif parsed_path == '/joinServer':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                invite_code = data.get('invite_code')

                if not invite_code:
                    self.send_error(400, "Missing invite_code")
                    return

                success, message, result = Events.join_server(invite_code, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "joined server",
                    "server_id": result['server_id'],
                })

            elif parsed_path == '/sendMessage':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                channel_id = data.get('channel_id')
                content = data.get('content')

                if not channel_id or not content:
                    self.send_error(400, "Missing channel_id or content")
                    return

                try:
                    channel_id = int(channel_id)
                except (ValueError, TypeError):
                    self.send_error(400, "channel_id must be an integer")
                    return

                success, message, result = Events.send_message(channel_id, user_token, content, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "message sent",
                    "message_id": result['message_id'],
                })

            elif parsed_path == '/sendDM':
                user_token = self._require_auth()
                if not user_token:
                    return

                data = self._read_json_body()
                recipient_id = data.get('recipient_id')
                content = data.get('content')

                if not recipient_id or not content:
                    self.send_error(400, "Missing recipient_id or content")
                    return

                try:
                    recipient_id = int(recipient_id)
                except (ValueError, TypeError):
                    self.send_error(400, "recipient_id must be an integer")
                    return

                success, message, result = Events.send_dm(recipient_id, user_token, content, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {
                    "status": "dm sent",
                    "message_id": result['message_id'],
                })

            else:
                self.send_error(404, "Not found")

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        if not self._db_guard():
            return
        assert self.db is not None
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            params = parse_qs(parsed.query)

            def param(key: str) -> str | None:
                values = params.get(key)
                return values[0] if values else None

            user_token = self._require_auth()
            if not user_token:
                return

            if path == '/getMessages':
                channel_id = param('channel_id')
                if not channel_id:
                    self.send_error(400, "Missing channel_id query parameter")
                    return

                try:
                    channel_id = int(channel_id)
                except (ValueError, TypeError):
                    self.send_error(400, "channel_id must be an integer")
                    return

                before_id = param('before')
                before = int(before_id) if before_id else None

                success, message, messages = Events.get_messages(channel_id, user_token, self.db, before)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"messages": messages})

            elif path == '/getServerMembers':
                server_id = param('server_id')
                if not server_id:
                    self.send_error(400, "Missing server_id query parameter")
                    return

                try:
                    server_id = int(server_id)
                except (ValueError, TypeError):
                    self.send_error(400, "server_id must be an integer")
                    return

                success, message, members = Events.get_server_members(server_id, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"members": members})

            elif path == '/getUser':
                user_id = param('user_id')
                if not user_id:
                    self.send_error(400, "Missing user_id query parameter")
                    return

                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    self.send_error(400, "user_id must be an integer")
                    return

                success, message, data = Events.get_user_by_id(user_id, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, data)

            elif path == '/getServer':
                server_id = param('server_id')
                if not server_id:
                    self.send_error(400, "Missing server_id query parameter")
                    return

                try:
                    server_id = int(server_id)
                except (ValueError, TypeError):
                    self.send_error(400, "server_id must be an integer")
                    return

                success, message, data = Events.get_server_by_id(server_id, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, data)

            elif path == '/getUsers':
                success, message, users = Events.get_all_users(user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"users": users})

            elif path == '/getUserServers':
                success, message, servers = Events.get_user_servers(user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"servers": servers})

            elif path == '/getDMList':
                success, message, dms = Events.get_dm_list(user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"dms": dms})

            elif path == '/getDMMessages':
                other_user_id = param('user_id')
                if not other_user_id:
                    self.send_error(400, "Missing user_id query parameter")
                    return

                try:
                    other_user_id = int(other_user_id)
                except (ValueError, TypeError):
                    self.send_error(400, "user_id must be an integer")
                    return

                before_id = param('before')
                before = int(before_id) if before_id else None

                success, message, messages = Events.get_dm_messages(other_user_id, user_token, self.db, before)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"messages": messages})

            elif path == '/getServerChannels':
                server_id = param('server_id')
                if not server_id:
                    self.send_error(400, "Missing server_id query parameter")
                    return

                try:
                    server_id = int(server_id)
                except (ValueError, TypeError):
                    self.send_error(400, "server_id must be an integer")
                    return

                success, message, channels = Events.get_server_channels(server_id, user_token, self.db)
                if not success:
                    self.send_error(400, message)
                    return

                self._send_json(200, {"channels": channels})

            else:
                self.send_error(404, "Not found")

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
