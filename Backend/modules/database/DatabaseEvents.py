from modules.database import Database
import secrets

def add_user(username, hashed_passwd, db: Database.FreecordDB) -> tuple[bool, str]:
    if not db:
        return False, "no database"

    if db().exists('users', {'username': username}):
        return False, "User already exists"
    
    try:
        user_token = f"FCT_{secrets.token_urlsafe(84)}"
        db().insert('users', {'username': username, 'hashed_passwd': hashed_passwd, 'user_token': user_token})
    except Exception as e:
        return False, f"Failed to add user: {e}"
    
    return True, "User added successfully"