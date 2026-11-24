"""Phase 34: std.sql module tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pealang.stdlib import build_standard_library


def test_sql_select():
    std = build_standard_library()['std']
    sql = std['sql']
    result = sql.select('users', ['id', 'name'], where="active = 1")
    assert result == 'SELECT id, name FROM users WHERE active = 1'


def test_sql_insert():
    std = build_standard_library()['std']
    sql = std.sql.insert('users', {'id': 1, 'name': 'Alice'})
    assert sql == "INSERT INTO users (id, name) VALUES (1, 'Alice')"


def test_sql_update():
    std = build_standard_library()['std']
    sql = std.sql.update('users', {'name': 'Bob'}, 'id = 1')
    assert sql == "UPDATE users SET name = 'Bob' WHERE id = 1"


def test_sql_delete():
    std = build_standard_library()['std']
    sql = std.sql.delete('users', 'id = 1')
    assert sql == "DELETE FROM users WHERE id = 1"


def test_sql_create_table():
    std = build_standard_library()['std']
    sql = std.sql.create_table('users', {'id': 'INT', 'name': 'TEXT'})
    assert sql == "CREATE TABLE IF NOT EXISTS users (id INT, name TEXT)"


def test_sql_drop_table():
    std = build_standard_library()['std']
    sql = std.sql.drop_table('users')
    assert sql == "DROP TABLE IF EXISTS users"
