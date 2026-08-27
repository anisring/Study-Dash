import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = 'study_dash.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        test_name TEXT NOT NULL,
        physics INTEGER NOT NULL,
        chemistry INTEGER NOT NULL,
        maths INTEGER NOT NULL,
        total INTEGER NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        target INTEGER NOT NULL,
        start_date TEXT,
        end_date TEXT,
        test_id INTEGER,
        FOREIGN KEY(test_id) REFERENCES tests(id)
    )
    ''')
    conn.commit()
    conn.close()


def add_test(date: str, test_name: str, physics: int, chemistry: int, maths: int) -> int:
    total = physics + chemistry + maths
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''INSERT INTO tests (date, test_name, physics, chemistry, maths, total)
                   VALUES (?, ?, ?, ?, ?, ?)''', (date, test_name, physics, chemistry, maths, total))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def update_test(tid: int, date: str, test_name: str, physics: int, chemistry: int, maths: int):
    total = physics + chemistry + maths
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''UPDATE tests SET date=?, test_name=?, physics=?, chemistry=?, maths=?, total=? WHERE id=?''',
                (date, test_name, physics, chemistry, maths, total, tid))
    conn.commit()
    conn.close()


def delete_test(tid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM tests WHERE id=?', (tid,))
    # detach any goals pointing to this test
    cur.execute('UPDATE goals SET test_id=NULL WHERE test_id=?', (tid,))
    conn.commit()
    conn.close()


def get_tests(order_desc: bool = False) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    order = 'DESC' if order_desc else 'ASC'
    cur.execute(f'SELECT * FROM tests ORDER BY date {order}, id {order}')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_test_by_id(tid: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM tests WHERE id=?', (tid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_goal(name: str, gtype: str, target: int, start_date: Optional[str], end_date: Optional[str], test_id: Optional[int]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''INSERT INTO goals (name, type, target, start_date, end_date, test_id)
                   VALUES (?, ?, ?, ?, ?, ?)''', (name, gtype, target, start_date, end_date, test_id))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid


def update_goal(gid: int, name: str, gtype: str, target: int, start_date: Optional[str], end_date: Optional[str], test_id: Optional[int]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''UPDATE goals SET name=?, type=?, target=?, start_date=?, end_date=?, test_id=? WHERE id=?''',
                (name, gtype, target, start_date, end_date, test_id, gid))
    conn.commit()
    conn.close()


def delete_goal(gid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM goals WHERE id=?', (gid,))
    conn.commit()
    conn.close()


def get_goals() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM goals ORDER BY start_date IS NULL, start_date')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def parse_date(s: str):
    try:
        return datetime.strptime(s, '%Y-%m-%d')
    except Exception:
        return None
