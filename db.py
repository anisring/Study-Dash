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
    cur.execute('''
    CREATE TABLE IF NOT EXISTS library_papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL UNIQUE,
        file_type TEXT NOT NULL,
        extracted_text TEXT NOT NULL,
        question_count INTEGER NOT NULL DEFAULT 0,
        difficulty TEXT NOT NULL DEFAULT 'Not enough data',
        uploaded_at TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL DEFAULT '',
        email TEXT NOT NULL DEFAULT '',
        avatar_name TEXT
    )
    ''')
    cur.execute('INSERT OR IGNORE INTO profile (id) VALUES (1)')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS exam_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        exam_date TEXT NOT NULL,
        exam_time TEXT,
        portions TEXT,
        reminder_sent_at TEXT
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


def get_profile() -> Dict:
    conn = get_conn()
    row = conn.execute('SELECT * FROM profile WHERE id=1').fetchone()
    conn.close()
    return dict(row) if row else {'id': 1, 'name': '', 'email': '', 'avatar_name': None}


def update_profile(name: str, email: str, avatar_name: Optional[str] = None):
    conn = get_conn()
    if avatar_name is None:
        conn.execute('UPDATE profile SET name=?, email=? WHERE id=1', (name, email))
    else:
        conn.execute('UPDATE profile SET name=?, email=?, avatar_name=? WHERE id=1', (name, email, avatar_name))
    conn.commit()
    conn.close()


def add_library_paper(original_name: str, stored_name: str, file_type: str, extracted_text: str,
                      question_count: int, difficulty: str, uploaded_at: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''INSERT INTO library_papers
                   (original_name, stored_name, file_type, extracted_text, question_count, difficulty, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (original_name, stored_name, file_type, extracted_text, question_count, difficulty, uploaded_at))
    conn.commit()
    paper_id = cur.lastrowid
    conn.close()
    return paper_id


def get_library_papers() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''SELECT id, original_name, file_type, question_count, difficulty, uploaded_at
                   FROM library_papers ORDER BY uploaded_at DESC, id DESC''')
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_library_paper(paper_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM library_papers WHERE id=?', (paper_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_library_paper(paper_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM library_papers WHERE id=?', (paper_id,))
    conn.commit()
    conn.close()


def add_exam_event(title: str, exam_date: str, exam_time: Optional[str], portions: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''INSERT INTO exam_events (title, exam_date, exam_time, portions)
                   VALUES (?, ?, ?, ?)''', (title, exam_date, exam_time, portions))
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id


def get_exam_events() -> List[Dict]:
    conn = get_conn()
    rows = [dict(row) for row in conn.execute('''SELECT * FROM exam_events
        ORDER BY exam_date ASC, exam_time ASC, id ASC''').fetchall()]
    conn.close()
    return rows


def get_exam_event(event_id: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute('SELECT * FROM exam_events WHERE id=?', (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_exam_event(event_id: int):
    conn = get_conn()
    conn.execute('DELETE FROM exam_events WHERE id=?', (event_id,))
    conn.commit()
    conn.close()


def mark_exam_reminded(event_id: int, sent_at: str):
    conn = get_conn()
    conn.execute('UPDATE exam_events SET reminder_sent_at=? WHERE id=?', (sent_at, event_id))
    conn.commit()
    conn.close()
