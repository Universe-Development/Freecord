import sqlite3
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import uuid

class MessagingServer(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_request_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            return json.loads(post_data.decode('utf-8'))
        except:
            return None
    
    def do_POST(self):
        path = self.path
        if path == '/users':
            self.create_user()
        elif path == '/servers':
            self.create_server()
        elif path.startswith('/servers/') and path.endswith('/join'):
            server_id = path.split('/')[2]
            self.join_server(server_id)
        elif path.startswith('/servers/') and path.endswith('/messages'):
            server_id = path.split('/')[2]
            self.send_server_message(server_id)
        elif path == '/direct_messages':
            self.send_direct_message()
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def do_GET(self):
        path = self.path
        if path == '/users':
            self.get_users()
        elif path.startswith('/users/'):
            user_id = path.split('/')[2]
            self.get_user(user_id)
        elif path.startswith('/servers/') and '/messages' in path:
            parts = path.split('/')
            server_id = parts[2]
            self.get_server_messages(server_id)
        elif path.startswith('/direct_messages/'):
            parts = path.split('/')
            if len(parts) >= 4:
                user1_id = parts[2]
                user2_id = parts[3]
                self.get_direct_messages(user1_id, user2_id)
            else:
                self.send_json_response({'error': 'Invalid path'}, 400)
        elif path == '/servers':
            self.get_servers()
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def create_user(self):
        data = self.get_request_data()
        if not data or 'username' not in data:
            self.send_json_response({'error': 'Username is required'}, 400)
            return
        username = data['username']
        user_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, username, created_at) 
                VALUES (?, ?, ?)
            ''', (user_id, username, created_at))
            conn.commit()
            conn.close()
            self.send_json_response({
                'id': user_id,
                'username': username,
                'created_at': created_at
            }, 201)
        except sqlite3.IntegrityError:
            self.send_json_response({'error': 'Username already exists'}, 409)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_users(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            users = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json_response({'users': users})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_user(self, user_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            if user:
                self.send_json_response(dict(user))
            else:
                self.send_json_response({'error': 'User not found'}, 404)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def create_server(self):
        data = self.get_request_data()
        if not data or 'name' not in data or 'owner_id' not in data:
            self.send_json_response({'error': 'Name and owner_id are required'}, 400)
            return
        name = data['name']
        owner_id = data['owner_id']
        server_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO servers (id, name, owner_id, created_at) 
                VALUES (?, ?, ?, ?)
            ''', (server_id, name, owner_id, created_at))
            cursor.execute('''
                INSERT INTO server_members (server_id, user_id, joined_at) 
                VALUES (?, ?, ?)
            ''', (server_id, owner_id, created_at))
            conn.commit()
            conn.close()
            self.send_json_response({
                'id': server_id,
                'name': name,
                'owner_id': owner_id,
                'created_at': created_at
            }, 201)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_servers(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers')
            servers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json_response({'servers': servers})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def join_server(self, server_id):
        data = self.get_request_data()
        if not data or 'user_id' not in data:
            self.send_json_response({'error': 'user_id is required'}, 400)
            return
        user_id = data['user_id']
        joined_at = datetime.now().isoformat()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_members (server_id, user_id, joined_at) 
                VALUES (?, ?, ?)
            ''', (server_id, user_id, joined_at))
            conn.commit()
            conn.close()
            self.send_json_response({'message': 'Joined server successfully'})
        except sqlite3.IntegrityError:
            self.send_json_response({'error': 'Already a member of this server'}, 409)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def send_server_message(self, server_id):
        data = self.get_request_data()
        if not data or 'user_id' not in data or 'content' not in data:
            self.send_json_response({'error': 'user_id and content are required'}, 400)
            return
        user_id = data['user_id']
        content = data['content']
        message_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM server_members 
                WHERE server_id = ? AND user_id = ?
            ''', (server_id, user_id))
            if not cursor.fetchone():
                self.send_json_response({'error': 'User is not a member of this server'}, 403)
                return
            cursor.execute('''
                INSERT INTO server_messages (id, server_id, user_id, content, created_at) 
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, server_id, user_id, content, created_at))
            conn.commit()
            conn.close()
            self.send_json_response({
                'id': message_id,
                'server_id': server_id,
                'user_id': user_id,
                'content': content,
                'created_at': created_at
            }, 201)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_server_messages(self, server_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sm.*, u.username 
                FROM server_messages sm
                JOIN users u ON sm.user_id = u.id
                WHERE sm.server_id = ?
                ORDER BY sm.created_at ASC
            ''', (server_id,))
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json_response({'messages': messages})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def send_direct_message(self):
        data = self.get_request_data()
        if not data or 'sender_id' not in data or 'receiver_id' not in data or 'content' not in data:
            self.send_json_response({'error': 'sender_id, receiver_id, and content are required'}, 400)
            return
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        content = data['content']
        message_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO direct_messages (id, sender_id, receiver_id, content, created_at) 
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, sender_id, receiver_id, content, created_at))
            conn.commit()
            conn.close()
            self.send_json_response({
                'id': message_id,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'content': content,
                'created_at': created_at
            }, 201)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def get_direct_messages(self, user1_id, user2_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dm.*, 
                       s.username as sender_username,
                       r.username as receiver_username
                FROM direct_messages dm
                JOIN users s ON dm.sender_id = s.id
                JOIN users r ON dm.receiver_id = r.id
                WHERE (dm.sender_id = ? AND dm.receiver_id = ?)
                   OR (dm.sender_id = ? AND dm.receiver_id = ?)
                ORDER BY dm.created_at ASC
            ''', (user1_id, user2_id, user2_id, user1_id))
            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()
            self.send_json_response({'messages': messages})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

def init_db():
    conn = sqlite3.connect('messaging.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_members (
            server_id TEXT,
            user_id TEXT,
            joined_at TEXT NOT NULL,
            PRIMARY KEY (server_id, user_id),
            FOREIGN KEY (server_id) REFERENCES servers (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_messages (
            id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (server_id) REFERENCES servers (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS direct_messages (
            id TEXT PRIMARY KEY,
            sender_id TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('messaging.db')
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_db()
    server = HTTPServer(('localhost', 9764), MessagingServer)
    print("Messaging server running on http://localhost:9764")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
