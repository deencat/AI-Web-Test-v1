"""Reset database - drop and recreate all tables"""
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.init_db import init_db
from app.db.init_templates import seed_system_templates

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("Creating all tables...")
Base.metadata.create_all(bind=engine)

print("Initializing database...")
db = SessionLocal()
try:
    init_db(db)
    seed_system_templates(db)
finally:
    db.close()

print("Database reset complete!")
