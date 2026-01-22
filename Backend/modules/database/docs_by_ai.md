# FreecordDB Documentation

# Documentation made by clankers for FreecordDB

## Basic Usage

```python
from freecord_db import FreecordDB

db = FreecordDB("mydata")
```

This creates or opens a database file called `mydata.fcdb`.

## Table Operations

### Create a table

```python
db.create_table('users')
```

### Delete a table

```python
db.drop_table('users')
```

### List all tables

```python
tables = db.list_tables()
print(tables)
```

## Data Operations

### Insert data

```python
user_id = db.insert('users', {
    'username': 'alice',
    'email': 'alice@example.com',
    'status': 'online'
})
```

Returns the auto-generated row ID.

### Select data

Get all rows:

```python
users = db.select('users')
```

Get filtered rows:

```python
online_users = db.select('users', where={'status': 'online'})
alice = db.select('users', where={'username': 'alice'})
```

### Update data

```python
updated = db.update('users', 
    where={'username': 'alice'}, 
    data={'status': 'away'}
)
print(f"Updated {updated} rows")
```

### Delete data

```python
deleted = db.delete('users', where={'status': 'offline'})
print(f"Deleted {deleted} rows")
```

### Count rows

```python
total = db.count('users')
online = db.count('users', where={'status': 'online'})
```

## Database Info

```python
info = db.get_info()
print(info)
```

Returns:
- file: path to the database file
- tables: number of tables
- table_info: row count for each table
- file_size: size in bytes

## Closing

```python
db.close()
```

Saves the database. The database auto-saves after every operation, but you can call close() explicitly.

## Complete Example

```python
from freecord_db import FreecordDB

db = FreecordDB("chat_data")

db.create_table('users')
db.create_table('messages')

user_id = db.insert('users', {
    'username': 'bob',
    'email': 'bob@freecord.com'
})

db.insert('messages', {
    'user_id': user_id,
    'channel': 'general',
    'content': 'Hello world',
    'timestamp': '2025-01-22T10:30:00'
})

messages = db.select('messages', where={'channel': 'general'})
for msg in messages:
    print(msg)

db.update('users', 
    where={'username': 'bob'}, 
    data={'email': 'bob.new@freecord.com'}
)

db.close()
```

## Notes

- Every row automatically gets an 'id' field starting from 0
- All data is compressed with zlib level 9
- Database saves automatically after each operation
- File format is .fcdb (compressed JSON)