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

def create_invite(server_id, user_token, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.create_invite(server_id, user_token, db)
    if not success:
        return False, message, {}

    return True, "Invite created", data

def join_server(invite_code, user_token, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.join_server(invite_code, user_token, db)
    if not success:
        return False, message, {}

    return True, "Joined server successfully", data

def send_message(channel_id, user_token, content, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.send_message(channel_id, user_token, content, db)
    if not success:
        return False, message, {}

    return True, "Message sent", data

def get_messages(channel_id, user_token, db: Database.FreecordDB, before: int | None = None) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_messages(channel_id, user_token, db, before)
    if not success:
        return False, message, []

    return True, "OK", data

def get_all_users(user_token, db: Database.FreecordDB) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_all_users(user_token, db)
    if not success:
        return False, message, []

    return True, "OK", data

def get_server_members(server_id, user_token, db: Database.FreecordDB) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_server_members(server_id, user_token, db)
    if not success:
        return False, message, []

    return True, "OK", data

def get_server_channels(server_id, user_token, db: Database.FreecordDB) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_server_channels(server_id, user_token, db)
    if not success:
        return False, message, []

    return True, "OK", data

def get_user_servers(user_token, db: Database.FreecordDB) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_user_servers(user_token, db)
    if not success:
        return False, message, []

    return True, "OK", data

def send_dm(recipient_id, user_token, content, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.send_dm(recipient_id, user_token, content, db)
    if not success:
        return False, message, {}

    return True, "DM sent", data

def get_dm_messages(other_user_id, user_token, db: Database.FreecordDB, before: int | None = None) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_dm_messages(other_user_id, user_token, db, before)
    if not success:
        return False, message, []

    return True, "OK", data

def get_user_by_id(user_id, user_token, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.get_user_by_id(user_id, user_token, db)
    if not success:
        return False, message, {}
    return True, "OK", data

def get_server_by_id(server_id, user_token, db: Database.FreecordDB) -> tuple[bool, str, dict]:
    success, message, data = DBEvents.get_server_by_id(server_id, user_token, db)
    if not success:
        return False, message, {}
    return True, "OK", data

def get_dm_list(user_token, db: Database.FreecordDB) -> tuple[bool, str, list]:
    success, message, data = DBEvents.get_dm_list(user_token, db)
    if not success:
        return False, message, []

    return True, "OK", data
