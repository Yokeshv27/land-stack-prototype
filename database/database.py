from __future__ import annotations
import json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data'/'land_stack.db'
def connect():
    # SQLite is a local-demo fallback with one writer; wait for a short write lock
    # instead of failing during harmless Streamlit reruns.
    DB.parent.mkdir(exist_ok=True)
    c=sqlite3.connect(DB, timeout=30, isolation_level=None)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=30000')
    return c
def init_db():
    c=connect(); c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL,failed_attempts INTEGER DEFAULT 0,locked_until TEXT);
    CREATE TABLE IF NOT EXISTS parcels(id INTEGER PRIMARY KEY,prototype_ulpin TEXT UNIQUE NOT NULL,owner_name TEXT NOT NULL,survey_number TEXT NOT NULL,khasra_number TEXT,khata_number TEXT,area REAL NOT NULL,area_unit TEXT NOT NULL,village TEXT NOT NULL,tehsil TEXT,district TEXT NOT NULL,state TEXT NOT NULL,land_use TEXT,latitude REAL,longitude REAL,geometry_json TEXT NOT NULL,verification_status TEXT DEFAULT 'PENDING',floors INTEGER DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,parcel_id INTEGER REFERENCES parcels(id),filename TEXT NOT NULL,path TEXT NOT NULL,mime_type TEXT NOT NULL,uploaded_by TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ocr_results(id INTEGER PRIMARY KEY,document_id INTEGER REFERENCES documents(id),raw_text TEXT,status TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS ai_extractions(id INTEGER PRIMARY KEY,document_id INTEGER REFERENCES documents(id),field_name TEXT,value TEXT,confidence REAL,needs_review INTEGER,reviewed_value TEXT,reviewed_by TEXT,reviewed_at TEXT,reason TEXT);
    CREATE TABLE IF NOT EXISTS validation_results(id INTEGER PRIMARY KEY,parcel_id INTEGER REFERENCES parcels(id),field_name TEXT,status TEXT,message TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS department_records(id INTEGER PRIMARY KEY,parcel_id INTEGER REFERENCES parcels(id),department TEXT NOT NULL,payload_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY,timestamp TEXT DEFAULT CURRENT_TIMESTAMP,username TEXT,role TEXT,action TEXT,parcel_id INTEGER,old_value TEXT,new_value TEXT,status TEXT);
    '''); c.commit(); c.close()
def audit(username, role, action, parcel_id=None, old=None, new=None, status='OK'):
    c=connect(); c.execute('INSERT INTO audit_logs(username,role,action,parcel_id,old_value,new_value,status) VALUES(?,?,?,?,?,?,?)',(username,role,action,parcel_id,json.dumps(old) if old else None,json.dumps(new) if new else None,status)); c.commit(); c.close()
