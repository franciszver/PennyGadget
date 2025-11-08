#!/usr/bin/env python3
"""Get demo user UUIDs from database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from src.config.database import get_db_session
from src.models.user import User

with get_db_session() as db:
    users = db.query(User).filter(User.email.like('demo_%@demo.com')).all()

    print("Demo User UUIDs:")
    print("{")
    for u in sorted(users, key=lambda x: x.email):
        print(f"  '{u.email}': '{str(u.id)}',")
    print("}")

