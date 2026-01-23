from modules.database import DatabaseEvents as DBEvents, Database

def create_account(username, hashed_passwd, db: Database.FreecordDB) -> tuple[bool, str]:
    success, message = DBEvents.add_user(username, hashed_passwd, db)
    if not success:
        return False, message

    return True, "Account created successfully"