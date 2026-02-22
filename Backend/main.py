from modules import ServerClasses
from modules.database import Database

PORT = 9042

server = ServerClasses.MessageServer()
db = Database.FreecordDB("freecord_data")

def main():
    if db.exists_table('users') == False:
        db.create_table('users')

    if db.exists_table('servers') == False:
        db.create_table('servers')

    if db.exists_table('channels') == False:
        db.create_table('channels')

    print("db info ", db.get_info())

    server.start(PORT, db)

if __name__ == "__main__":
    print(f"Server is running on port {PORT}. Press Ctrl+C to stop.")

    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping server...")
        db.close()
        server.stop()
        print("Server stopped. database saved")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.close()
        server.stop()
        print("Server stopped due to error. database saved")
