from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
from sqlalchemy import Column, Integer, Float, DateTime
from .database import Base  # Import Base from database.py

class StockData(Base):
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    datetime = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

class StockDataSchema(BaseModel):
    datetime: datetime
    open: float = Field(gt=0, description="Opening price")
    high: float = Field(gt=0, description="Highest price")
    low: float = Field(gt=0, description="Lowest price")
    close: float = Field(gt=0, description="Closing price")
    volume: int = Field(gt=0, description="Trading volume")

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: float, values) -> float:
        if "low" in values.data and v <= values.data["low"]:
            raise ValueError("high price must be greater than low price")
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: float, values) -> float:
        if v <= 0:
            raise ValueError("low price must be greater than 0")
        if "high" in values.data and v >= values.data["high"]:
            raise ValueError("low price must be less than high price")
        return v

    class Config:
        from_attributes = True 