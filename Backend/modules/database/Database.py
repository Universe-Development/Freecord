import json
import zlib
import os
import threading
from typing import Any, Dict, List, Optional


class FreecordDB:
    def __init__(self, db_path: str):
        self.db_path = db_path if db_path.endswith('.fcdb') else f"{db_path}.fcdb"
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self.load_or_create()
    
    def load_or_create(self) -> None:
        if os.path.exists(self.db_path):
            self._load_from_file()
        else:
            self.tables = {}
            self.save()
    
    def _load_from_file(self) -> None:
        try:
            with open(self.db_path, 'rb') as f:
                compressed_data = f.read()
            
            decompressed_data = zlib.decompress(compressed_data)
            self.tables = json.loads(decompressed_data.decode())
        except Exception as e:
            raise ValueError(f"Failed to load database m:{e}")
    
    def save(self) -> None:
        tmp_path = self.db_path + '.tmp'
        json_data = json.dumps(self.tables, indent=2).encode()
        compressed_data = zlib.compress(json_data, level=9)
        
        with self._lock:
            with open(tmp_path, 'wb') as f:
                f.write(compressed_data)
                f.flush()
                os.fsync(f.fileno())
            
            os.replace(tmp_path, self.db_path)
    
    def create_table(self, table_name: str) -> None:
        if table_name in self.tables:
            raise ValueError(f"table '{table_name}' already exists")
        
        self.tables[table_name] = []
        self.save()

    def exists_table(self, table_name: str) -> bool:
        if table_name in self.tables:
            return True
        return False
    
    def drop_table(self, table_name: str) -> None:
        if table_name not in self.tables:
            raise ValueError(f"table '{table_name}' doesn't exist")
        
        del self.tables[table_name]
        self.save()
    
    def list_tables(self) -> List[str]:
        return list(self.tables.keys())
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        if table_name not in self.tables:
            raise ValueError(f"table '{table_name}' doesn't exist")
        
        row_id = len(self.tables[table_name])
        row = {'id': row_id, **data}
        
        self.tables[table_name].append(row)
        self.save()
        return row_id
    
    def exists(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> bool:
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        rows = self.tables[table_name]
        if where is None:
            return len(rows) > 0
        
        for row in rows:
            if self._row_matches_conditions(row, where):
                return True
        return False
    
    def select(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if table_name not in self.tables:
            raise ValueError(f"table '{table_name}' is does not existent")
        
        rows = self.tables[table_name]
        
        if where is None:
            return rows.copy()
        
        return self._filter_rows(rows, where)
    
    def _filter_rows(self, rows: List[Dict[str, Any]], where: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = []
        for row in rows:
            if self._row_matches_conditions(row, where):
                result.append(row)
        return result
    
    def _row_matches_conditions(self, row: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        for key, value in conditions.items():
            if key not in row or row[key] != value:
                return False
        return True
    
    def update(self, table_name: str, where: Dict[str, Any], data: Dict[str, Any]) -> int:
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        count = 0
        for row in self.tables[table_name]:
            if self._row_matches_conditions(row, where):
                row.update(data)
                count += 1
        
        if count > 0:
            self.save()
        
        return count
    
    def delete(self, table_name: str, where: Dict[str, Any]) -> int:
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        
        original_count = len(self.tables[table_name])
        
        self.tables[table_name] = [
            row for row in self.tables[table_name]
            if not all(row.get(k) == v for k, v in where.items())
        ]
        
        deleted_count = original_count - len(self.tables[table_name])
        
        if deleted_count > 0:
            self.save()
        
        return deleted_count
    
    def count(self, table_name: str, where: Optional[Dict[str, Any]] = None) -> int:
        return len(self.select(table_name, where))
    
    def close(self) -> None:
        self.save()
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'file': self.db_path,
            'tables': len(self.tables),
            'table_info': {
                name: len(rows) for name, rows in self.tables.items()
            },
            'file_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        }