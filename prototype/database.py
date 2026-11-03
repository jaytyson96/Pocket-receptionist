"""SQLite storage for fictional ONECALL demo enquiries. Local use only."""
import json, sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from pricing import DEFAULT_RATES,validate_rates

def stamp(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

@contextmanager
def connection(path):
    db=sqlite3.connect(str(path),timeout=5)
    try:
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        with db: yield db
    finally: db.close()

def init(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with connection(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS pricing (
            business_id TEXT PRIMARY KEY, rates_json TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL, postcode TEXT NOT NULL, description TEXT NOT NULL,
            job_json TEXT NOT NULL, estimate_json TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('awaiting_owner','approved','rejected')),
            approved_total_pence INTEGER, owner_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        db.execute('INSERT OR IGNORE INTO pricing VALUES (?,?,?)',
                   ('premium-pressure-demo',json.dumps(DEFAULT_RATES),stamp()))

def rates(path):
    with connection(path) as db:
        row=db.execute('SELECT rates_json FROM pricing WHERE business_id=?',
                       ('premium-pressure-demo',)).fetchone()
        return validate_rates(json.loads(row['rates_json']))

def change_rates(path,new):
    checked=validate_rates(new)
    with connection(path) as db:
        db.execute('UPDATE pricing SET rates_json=?,updated_at=? WHERE business_id=?',
                   (json.dumps(checked),stamp(),'premium-pressure-demo'))
    return checked

def decode(row):
    if not row: return None
    item=dict(row)
    item['job']=json.loads(item.pop('job_json'))
    item['estimate']=json.loads(item.pop('estimate_json'))
    return item

def add(path,enquiry,draft):
    now=stamp()
    with connection(path) as db:
        cur=db.execute("""INSERT INTO enquiries
          (customer_name,postcode,description,job_json,estimate_json,status,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?)""",
          (enquiry['customer_name'],enquiry['postcode'],enquiry['description'],
           json.dumps(enquiry['job']),json.dumps(draft),'awaiting_owner',now,now))
        return decode(db.execute('SELECT * FROM enquiries WHERE id=?',(cur.lastrowid,)).fetchone())

def get(path,id):
    with connection(path) as db:
        return decode(db.execute('SELECT * FROM enquiries WHERE id=?',(id,)).fetchone())

def list_all(path):
    with connection(path) as db:
        return [decode(r) for r in db.execute('SELECT * FROM enquiries ORDER BY id DESC LIMIT 100')]

def review(path,id,status,approved_total_pence=None,note=''):
    if status not in ('approved','rejected'): raise ValueError('Invalid review status')
    with connection(path) as db:
        row=db.execute('SELECT status FROM enquiries WHERE id=?',(id,)).fetchone()
        if not row: return None,'missing'
        if row['status']!='awaiting_owner': return None,'already_reviewed'
        db.execute("""UPDATE enquiries
          SET status=?, approved_total_pence=?, owner_note=?, updated_at=?
          WHERE id=? AND status='awaiting_owner'""",
          (status,approved_total_pence,note,stamp(),id))
        return decode(db.execute('SELECT * FROM enquiries WHERE id=?',(id,)).fetchone()),None
