from modules.database import Database
from modules.database.IDManager import SnowflakeIDGenerator
import secrets
import time

"""
int('1' + str(SnowflakeIDGenerator.generate_id))

the 1st number is what type of id is this for.
This is the whole list
1 - Users
2 - Servers
3 - Channels
4 - Messages
5 - DM Channels
6 - DM Messages
"""

_token_cache: dict[str, dict] = {}

def _resolve_user(user_token: str, db: Database.FreecordDB) -> dict | None:
    if user_token in _token_cache:
        return _token_cache[user_token]
    users = db.select('users', {'user_token': user_token})
    if not users:
        return None
    _token_cache[user_token] = users[0]
    return users[0]

def _is_member(server_id: int, user_id: int, db: Database.FreecordDB) -> bool:
    return db.exists('members', {'server_id': server_id, 'user_id': user_id})

def _add_member(server_id: int, user_id: int, db: Database.FreecordDB) -> tuple[bool, str]:
    if _is_member(server_id, user_id, db):
        return False, "User is already a member of this server"
    db.insert('members', {'server_id': server_id, 'user_id': user_id})
    return True, "Member added"

def _get_or_create_dm_channel(user_id_a: int, user_id_b: int, db: Database.FreecordDB) -> int:
    lo, hi = min(user_id_a, user_id_b), max(user_id_a, user_id_b)
    existing = db.select('dm_channels', {'user1_id': lo, 'user2_id': hi})
    if existing:
        return existing[0]['dm_channel_id']
    dm_channel_id = int('5' + str(SnowflakeIDGenerator().generate_id()))
    db.insert('dm_channels', {'dm_channel_id': dm_channel_id, 'user1_id': lo, 'user2_id': hi}, save=False)
    return dm_channel_id

def add_user(username: str, hashed_passwd: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    if db.exists('users', {'username': username}):
        return False, "User already exists", {}

    try:
        user_token = f"FCT_{secrets.token_urlsafe(84)}"
        user_id = int('1' + str(SnowflakeIDGenerator().generate_id()))
        db.insert('users', {
            'username': username,
            'hashed_passwd': hashed_passwd,
            'user_token': user_token,
            'user_id': user_id,
        })
    except Exception as e:
        return False, f"Failed to add user: {e}", {}

    return True, "User added successfully", {'user_id': user_id, 'user_token': user_token}

def add_server(name: str, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    try:
        server_id = int('2' + str(SnowflakeIDGenerator().generate_id()))
        db.insert('servers', {
            'name': name,
            'server_id': server_id,
            'owner_id': user['user_id'],
        }, save=False)
        _add_member(server_id, user['user_id'], db)
    except Exception as e:
        return False, f"Failed to create server: {e}", {}

    return True, "Server created successfully", {'server_id': server_id}

def get_user_servers(user_token: str, db: Database.FreecordDB) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    memberships = db.select('members', {'user_id': user['user_id']})
    if not memberships:
        return True, "OK", []

    member_server_ids = {m['server_id'] for m in memberships}
    all_servers = db.select('servers', None)
    server_map = {s['server_id']: s for s in all_servers if s['server_id'] in member_server_ids}

    result = [
        {
            'server_id': s['server_id'],
            'name': s['name'],
            'is_owner': s['owner_id'] == user['user_id'],
        }
        for s in server_map.values()
    ]
    return True, "OK", result

def add_channel(name: str, server_id: int, user_token: str, channel_type: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    server_list = db.select('servers', {'server_id': server_id})
    if not server_list:
        return False, "Server not found", {}

    if server_list[0]['owner_id'] != user['user_id']:
        return False, "Only the server owner can create channels", {}

    if db.exists('channels', {'name': name, 'server_id': server_id}):
        return False, "A channel with that name already exists in this server", {}

    try:
        channel_id = int('3' + str(SnowflakeIDGenerator().generate_id()))
        db.insert('channels', {
            'name': name,
            'channel_id': channel_id,
            'server_id': server_id,
            'channel_type': channel_type,
        })
    except Exception as e:
        return False, f"Failed to create channel: {e}", {}

    return True, "Channel created successfully", {'channel_id': channel_id}

def get_server_channels(server_id: int, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    if not db.exists('servers', {'server_id': server_id}):
        return False, "Server not found", []

    if not _is_member(server_id, user['user_id'], db):
        return False, "You are not a member of this server", []

    channels = db.select('channels', {'server_id': server_id})
    return True, "OK", [
        {'channel_id': c['channel_id'], 'name': c['name'], 'channel_type': c['channel_type']}
        for c in channels
    ]

def create_invite(server_id: int, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    if not db.exists('servers', {'server_id': server_id}):
        return False, "Server not found", {}

    if not _is_member(server_id, user['user_id'], db):
        return False, "You are not a member of this server", {}

    try:
        invite_code = secrets.token_urlsafe(8)
        db.insert('invites', {
            'invite_code': invite_code,
            'server_id': server_id,
            'creator_id': user['user_id'],
        })
    except Exception as e:
        return False, f"Failed to create invite: {e}", {}

    return True, "Invite created", {'invite_code': invite_code}

def join_server(invite_code: str, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    invite_list = db.select('invites', {'invite_code': invite_code})
    if not invite_list:
        return False, "Invalid invite code", {}

    server_id = invite_list[0]['server_id']

    if _is_member(server_id, user['user_id'], db):
        return False, "You are already a member of this server", {}

    success, message = _add_member(server_id, user['user_id'], db)
    if not success:
        return False, message, {}

    return True, "Joined server successfully", {'server_id': server_id}

def get_server_members(server_id: int, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    server_list = db.select('servers', {'server_id': server_id})
    if not server_list:
        return False, "Server not found", []

    if not _is_member(server_id, user['user_id'], db):
        return False, "You are not a member of this server", []

    owner_id = server_list[0]['owner_id']
    member_records = db.select('members', {'server_id': server_id})
    member_ids = {m['user_id'] for m in member_records}

    all_users = db.select('users', None)
    user_map = {u['user_id']: u for u in all_users if u['user_id'] in member_ids}

    return True, "OK", [
        {
            'user_id': u['user_id'],
            'username': u['username'],
            'is_owner': u['user_id'] == owner_id,
        }
        for u in user_map.values()
    ]

def send_message(channel_id: int, user_token: str, content: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    if not content or not content.strip():
        return False, "Message content cannot be empty", {}

    channel_list = db.select('channels', {'channel_id': channel_id})
    if not channel_list:
        return False, "Channel not found", {}

    server_id = channel_list[0]['server_id']

    if not _is_member(server_id, user['user_id'], db):
        return False, "You are not a member of this server", {}

    try:
        message_id = int('4' + str(SnowflakeIDGenerator().generate_id()))
        db.insert('messages', {
            'message_id': message_id,
            'channel_id': channel_id,
            'server_id': server_id,
            'author_id': user['user_id'],
            'author_name': user['username'],
            'content': content.strip(),
            'timestamp': int(time.time()),
        })
    except Exception as e:
        return False, f"Failed to send message: {e}", {}

    return True, "Message sent", {'message_id': message_id}

def get_messages(channel_id: int, user_token: str, db: Database.FreecordDB, before: int | None = None) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    channel_list = db.select('channels', {'channel_id': channel_id})
    if not channel_list:
        return False, "Channel not found", []

    if not _is_member(channel_list[0]['server_id'], user['user_id'], db):
        return False, "You are not a member of this server", []

    messages = db.select('messages', {'channel_id': channel_id})

    if before is not None:
        idx = next((i for i, m in enumerate(messages) if m['message_id'] == before), None)
        if idx is not None:
            messages = messages[:idx]

    return True, "OK", [
        {
            'message_id': m['message_id'],
            'author_id': m['author_id'],
            'content': m['content'],
            'timestamp': m['timestamp'],
        }
        for m in messages[-50:]
    ]

def get_user_by_id(user_id: int, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    if _resolve_user(user_token, db) is None:
        return False, "Invalid user token", {}

    result = db.select('users', {'user_id': user_id})
    if not result:
        return False, "User not found", {}

    u = result[0]
    return True, "OK", {'user_id': u['user_id'], 'username': u['username']}

def get_server_by_id(server_id: int, user_token: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    if _resolve_user(user_token, db) is None:
        return False, "Invalid user token", {}

    result = db.select('servers', {'server_id': server_id})
    if not result:
        return False, "Server not found", {}

    s = result[0]
    member_count = db.count('members', {'server_id': server_id})
    channel_count = db.count('channels', {'server_id': server_id})
    owner = db.select('users', {'user_id': s['owner_id']})
    owner_name = owner[0]['username'] if owner else "unknown"

    return True, "OK", {
        'server_id': s['server_id'],
        'name': s['name'],
        'owner_id': s['owner_id'],
        'owner_name': owner_name,
        'member_count': member_count,
        'channel_count': channel_count,
    }

def get_all_users(user_token: str, db: Database.FreecordDB) -> tuple[bool, str, list]:
    if _resolve_user(user_token, db) is None:
        return False, "Invalid user token", []

    return True, "OK", [
        {'user_id': u['user_id'], 'username': u['username']}
        for u in db.select('users', None)
    ]

def send_dm(recipient_id: int, user_token: str, content: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    if not content or not content.strip():
        return False, "Message content cannot be empty", {}

    if user['user_id'] == recipient_id:
        return False, "You cannot DM yourself", {}

    if not db.exists('users', {'user_id': recipient_id}):
        return False, "Recipient not found", {}

    try:
        dm_channel_id = _get_or_create_dm_channel(user['user_id'], recipient_id, db)
        message_id = int('6' + str(SnowflakeIDGenerator().generate_id()))
        db.insert('dm_messages', {
            'message_id': message_id,
            'dm_channel_id': dm_channel_id,
            'author_id': user['user_id'],
            'author_name': user['username'],
            'content': content.strip(),
            'timestamp': int(time.time()),
        })
    except Exception as e:
        return False, f"Failed to send DM: {e}", {}

    return True, "DM sent", {'message_id': message_id}

def get_dm_messages(other_user_id: int, user_token: str, db: Database.FreecordDB, before: int | None = None) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    if not db.exists('users', {'user_id': other_user_id}):
        return False, "User not found", []

    lo, hi = min(user['user_id'], other_user_id), max(user['user_id'], other_user_id)
    dm_channel = db.select('dm_channels', {'user1_id': lo, 'user2_id': hi})
    if not dm_channel:
        return True, "OK", []

    messages = db.select('dm_messages', {'dm_channel_id': dm_channel[0]['dm_channel_id']})

    if before is not None:
        idx = next((i for i, m in enumerate(messages) if m['message_id'] == before), None)
        if idx is not None:
            messages = messages[:idx]

    return True, "OK", [
        {
            'message_id': m['message_id'],
            'author_id': m['author_id'],
            'content': m['content'],
            'timestamp': m['timestamp'],
        }
        for m in messages[-50:]
    ]

def get_dm_list(user_token: str, db: Database.FreecordDB) -> tuple[bool, str, list]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", []

    uid = user['user_id']
    all_channels = db.select('dm_channels', None)
    my_channels = [c for c in all_channels if c['user1_id'] == uid or c['user2_id'] == uid]
    if not my_channels:
        return True, "OK", []

    other_ids = {
        (c['user2_id'] if c['user1_id'] == uid else c['user1_id'])
        for c in my_channels
    }
    all_users = db.select('users', None)
    user_map = {u['user_id']: u for u in all_users if u['user_id'] in other_ids}

    result = []
    for c in my_channels:
        other_id = c['user2_id'] if c['user1_id'] == uid else c['user1_id']
        other = user_map.get(other_id)
        if not other:
            continue
        result.append({
            'dm_channel_id': c['dm_channel_id'],
            'user_id': other['user_id'],
            'username': other['username'],
        })

    return True, "OK", result