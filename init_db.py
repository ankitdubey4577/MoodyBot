# init_db.py
from sqlalchemy import inspect
from src.db.database import Base, engine

import src.db.models  # IMPORTANT: ensures Event/Task/etc are registered

def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    print("Database tables created successfully")
    print("Tables in DB:", inspector.get_table_names())

if __name__ == "__main__":
    init_db()
