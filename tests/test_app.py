import sys
import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.models import StockData, StockDataSchema

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def load_csv_data_for_test(db):
    """Load data from the CSV file into test database"""
    csv_file = r"C:\Users\DELL\Downloads\stock_data.csv"
    df = pd.read_csv(csv_file)

    # Print column names to debug
    print("CSV columns:", df.columns.tolist())

    # Map column names to expected names
    column_mapping = {
        "datetime": "datetime",  # Update these based on your actual CSV columns
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }

    for _, row in df.iterrows():
        db_data = StockData(
            datetime=pd.to_datetime(row[column_mapping["datetime"]]),
            open=float(row[column_mapping["open"]]),
            high=float(row[column_mapping["high"]]),
            low=float(row[column_mapping["low"]]),
            close=float(row[column_mapping["close"]]),
            volume=int(row[column_mapping["volume"]]),
        )
        db.add(db_data)
    db.commit()
    return len(df)


def test_with_csv_data(test_db):
    """Test the application with actual CSV data"""
    # Load CSV data
    db = TestingSessionLocal()
    num_records = load_csv_data_for_test(db)
    print(f"Loaded {num_records} records from CSV")

    # Test GET /data endpoint
    response = client.get("/data")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == num_records
    print(f"Successfully retrieved {len(data)} records from API")

    # Test strategy performance
    response = client.get("/strategy/performance")
    assert response.status_code == 200
    performance = response.json()
    assert "total_returns" in performance
    assert "sharpe_ratio" in performance
    assert "number_of_trades" in performance
    print("Strategy Performance:")
    print(f"Total Returns: {performance['total_returns']:.2f}")
    print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
    print(f"Number of Trades: {performance['number_of_trades']}")


def test_create_data(test_db):
    response = client.post(
        "/data",
        json={
            "datetime": "2023-01-01T00:00:00",
            "open": 100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 1000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["close"] == 105.0


def test_create_invalid_data(test_db):
    response = client.post(
        "/data",
        json={
            "datetime": "invalid-date",
            "open": -100.0,  # Invalid negative price
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 1000,
        },
    )
    assert response.status_code == 422


def test_get_data(test_db):
    # Add test data
    db = TestingSessionLocal()
    db_data = StockData(
        datetime=datetime(2023, 1, 1),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1000,
    )
    db.add(db_data)
    db.commit()

    response = client.get("/data")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["close"] == 105.0


def test_strategy_performance(test_db):
    # Add test data with increasing prices
    db = TestingSessionLocal()
    base_price = 100.0
    for i in range(60):
        price = base_price + i
        db_data = StockData(
            datetime=datetime(2023, 1, 1) + timedelta(days=i),
            open=price,
            high=price + 10,
            low=price - 10,
            close=price,
            volume=1000,
        )
        db.add(db_data)
    db.commit()

    response = client.get("/strategy/performance")
    assert response.status_code == 200
    data = response.json()
    assert "total_returns" in data
    assert "sharpe_ratio" in data
    assert "number_of_trades" in data
    assert isinstance(data["total_returns"], float)
    assert isinstance(data["sharpe_ratio"], float)
    assert isinstance(data["number_of_trades"], int)


def test_strategy_performance_insufficient_data(test_db):
    # Add only a few data points (less than required for strategy)
    db = TestingSessionLocal()
    db_data = StockData(
        datetime=datetime(2023, 1, 1),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1000,
    )
    db.add(db_data)
    db.commit()

    response = client.get("/strategy/performance")
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough data points"


def test_invalid_strategy_request(test_db):
    """Test strategy endpoint with invalid data"""
    response = client.get("/strategy/performance")
    assert response.status_code == 400
    assert "Not enough data points" in response.json()["detail"]


def test_data_validation(test_db):
    """Test data validation in POST endpoint"""
    invalid_data = [
        # Test case 0: Invalid date format
        {
            "datetime": "invalid-date",
            "open": 100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 1000,
        },
        # Test case 1: Negative price
        {
            "datetime": "2023-01-01T00:00:00",
            "open": -100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 1000,
        },
        # Test case 2: High price less than low price
        {
            "datetime": "2023-01-01T00:00:00",
            "open": 100.0,
            "high": 80.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 1000,
        },
        # Test case 3: Zero volume
        {
            "datetime": "2023-01-01T00:00:00",
            "open": 100.0,
            "high": 110.0,
            "low": 90.0,
            "close": 105.0,
            "volume": 0,
        },
    ]

    for i, data in enumerate(invalid_data):
        response = client.post("/data", json=data)
        assert (
            response.status_code == 422
        ), f"Test case {i} failed: Expected 422 but got {response.status_code}"
        error_detail = response.json().get("detail", [])
        print(f"Test case {i} error details: {error_detail}")


def test_database_connection(test_db):
    """Test database connection and operations"""
    db = TestingSessionLocal()
    try:
        # Test database write
        db_data = StockData(
            datetime=datetime(2023, 1, 1),
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1000,
        )
        db.add(db_data)
        db.commit()

        # Test database read
        data = db.query(StockData).first()
        assert data is not None
        assert data.open == 100.0

    finally:
        db.close()
