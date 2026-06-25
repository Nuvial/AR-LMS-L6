import os
import sqlite3
from flask import g

def get_db():
    if 'db' not in g:
        os.makedirs('data', exist_ok=True)
        g.db = sqlite3.connect('data/database.db')
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db