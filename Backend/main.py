from modules import ServerClasses
from modules.database import Database
import http.server
import time

PORT = 9042

server = ServerClasses.MessageServer()
db = Database.FreecordDB("freecord_data")

def main():
    if 'users' not in db.list_tables():
        db.create_table('users')
    
    print("db info ", db.get_info())

    server.start(PORT)

if __name__ == "__main__":
    print(f"Server is running on port {PORT}. Press Ctrl+C to stop.")

    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping server...")
        db.close()
        server.stop()
        print("Server stopped. database saved")