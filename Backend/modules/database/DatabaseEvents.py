from modules.database import Database
from modules.database.IDManager import SnowflakeIDGenerator
import secrets

"""
int('1' + str(SnowflakeIDGenerator.generate_id))

the 1st number is what type of id is this for.
This is the whole list
1 - Users
2 - Servers
"""

def add_user(username, hashed_passwd, db: Database.FreecordDB) -> tuple[bool, str]:
    if not db:
        return False, "no database"

    if db().exists('users', {'username': username}):
        return False, "User already exists"
    
    try:
        user_token = f"FCT_{secrets.token_urlsafe(84)}"
        user_id = int('1' + str(SnowflakeIDGenerator.generate_id))
        db().insert('users', {'username': username, 'hashed_passwd': hashed_passwd, 'user_token': user_token, 'user_id': user_id})
    except Exception as e:
        return False, f"Failed to add user: {e}"
    
    return True, "User added successfully"

def add_server(name, db : Database.FreecordDB) -> tuple[bool, str]:
    if not db:
        return False, "no database"
    
    try:
        server_id = int('2' + str(SnowflakeIDGenerator.generate_id))
    except Exception as e:
        return False, f"Failed to create server: {e}"
    
    return True, "Server created successfully"