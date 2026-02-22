from modules.database import Database
from modules.database.IDManager import SnowflakeIDGenerator
import secrets

"""
int('1' + str(SnowflakeIDGenerator.generate_id))

the 1st number is what type of id is this for.
This is the whole list
1 - Users
2 - Servers
3 - Channels
"""

def _resolve_user(user_token: str, db: Database.FreecordDB) -> dict | None:
    """Returns the user record matching the token, or None if invalid."""
    users = db.select('users', {'user_token': user_token})
    return users[0] if users else None

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
        })
    except Exception as e:
        return False, f"Failed to create server: {e}", {}

    return True, "Server created successfully", {'server_id': server_id}

def add_channel(name: str, server_id: int, user_token: str, channel_type: str, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    user = _resolve_user(user_token, db)
    if user is None:
        return False, "Invalid user token", {}

    server_list = db.select('servers', {'server_id': server_id})
    if not server_list:
        return False, "Server not found", {}

    server = server_list[0]
    if server['owner_id'] != user['user_id']:
        return False, "You do not have permission to create channels in this server", {}

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