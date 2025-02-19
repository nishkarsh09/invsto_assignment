import pytest
import pandas as pd
from datetime import datetime
from app.load_data import load_csv_data
from app.database import get_db, Base, engine
from app.models import StockData
import os
from sqlalchemy import text

@pytest.fixture
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Clear all data from tables
    db = next(get_db())
    try:
        db.execute(text('DELETE FROM stock_data'))
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_load_csv_data(setup_database):
    # Create a temporary test CSV file
    test_data = pd.DataFrame({
        'datetime': ['2023-01-01', '2023-01-02'],
        'open': [100.0, 101.0],
        'high': [110.0, 111.0],
        'low': [90.0, 91.0],
        'close': [105.0, 106.0],
        'volume': [1000, 1100]
    })
    
    test_csv_path = 'test_data.csv'
    try:
        # Save test data to CSV
        test_data.to_csv(test_csv_path, index=False)
        
        # Test loading data
        num_records = load_csv_data(test_csv_path)
        assert num_records == 2
        
        # Verify data in database
        db = next(get_db())
        try:
            data = db.query(StockData).all()
            assert len(data) == 2
            
            # Check first record
            first_record = data[0]
            assert first_record.open == 100.0
            assert first_record.high == 110.0
            assert first_record.low == 90.0
            assert first_record.close == 105.0
            assert first_record.volume == 1000
            
        finally:
            db.close()
            
    finally:
        # Cleanup
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)

def test_load_csv_invalid_file(setup_database):
    with pytest.raises(Exception):
        load_csv_data("nonexistent_file.csv")

def test_load_csv_invalid_data(setup_database):
    # Create CSV with invalid data
    test_data = pd.DataFrame({
        'datetime': ['invalid_date'],
        'open': ['invalid'],
        'high': [110.0],
        'low': [90.0],
        'close': [105.0],
        'volume': [1000]
    })
    
    test_csv_path = 'invalid_test_data.csv'
    try:
        test_data.to_csv(test_csv_path, index=False)
        with pytest.raises(Exception):
            load_csv_data(test_csv_path)
    finally:
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path) 