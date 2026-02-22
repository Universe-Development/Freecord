from modules.database import DatabaseEvents as DBEvents, Database

def create_account(username, hashed_passwd, db: Database.FreecordDB) -> tuple[bool, str]:
    success, message, _ = DBEvents.add_user(username, hashed_passwd, db)
    if not success:
        return False, message

    return True, "Account created successfully"

def create_server(name, user_token, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.add_server(name, user_token, db)
    if not success:
        return False, message, {}

    return True, "Server created successfully", data

def create_channel(name, server_id, user_token, db: Database.FreecordDB, channel_type: str = "text") -> tuple[bool, str, dict]:
    success, message, data = DBEvents.add_channel(name, server_id, user_token, channel_type, db)
    if not success:
        return False, message, {}

    return True, "Channel created successfully", data