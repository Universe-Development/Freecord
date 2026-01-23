from modules.database import Database

def add_user(username, hashed_passwd, db: Database.FreecordDB) -> tuple[bool, str]:
    if not db:
        return False, "no database"

    if db().exists('users', {'username': username}):
        return False, "User already exists"
    
    db().insert('users', {'username': username, 'hashed_passwd': hashed_passwd})
    
    return True, "User added successfully"