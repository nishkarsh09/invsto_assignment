from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Create the base class for declarative models
Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")
# Add this line for debugging
print(f"Connecting to database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 