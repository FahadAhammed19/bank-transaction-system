"""Restore the fictional sample SQL database without overwriting existing data."""
from pathlib import Path
import sqlite3
root=Path(__file__).resolve().parent
out=root/'db.sqlite3'
if out.exists():
    raise SystemExit('db.sqlite3 already exists. Back it up or choose the migrate/seed route instead.')
try:
    with sqlite3.connect(out) as db:
        db.executescript((root/'sample_data/demo.sql').read_text())
except Exception:
    out.unlink(missing_ok=True)
    raise
print('Restored fictional sample database. Login: demo / DemoPass!2026')
