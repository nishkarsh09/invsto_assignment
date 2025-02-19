import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, StockData
import os
from dotenv import load_dotenv

load_dotenv()


def load_csv_data(file_path: str):
    """Load data from CSV file into database"""
    try:
        # Read CSV file
        print(f"Loading data from: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Found {len(df)} records")

        # Print column names for debugging
        print("CSV columns:", df.columns.tolist())

        # Connect to database
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"Connecting to database: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Convert data and insert into database
            for _, row in df.iterrows():
                stock_data = StockData(
                    datetime=pd.to_datetime(row["datetime"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                )
                db.add(stock_data)

            db.commit()
            print(f"Successfully loaded {len(df)} records")
            return len(df)
        except Exception as e:
            print(f"Error loading data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    # Direct path to your downloaded CSV file
    csv_file = r"C:\Users\DELL\Downloads\stock_data.csv"
    load_csv_data(csv_file)
