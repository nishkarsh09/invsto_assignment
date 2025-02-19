from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, database, strategy

app = FastAPI()

# Create tables
models.Base.metadata.create_all(bind=database.engine)

@app.get("/data")
def get_data(db: Session = Depends(database.get_db)):
    return db.query(models.StockData).all()

@app.post("/data")
def add_data(data: models.StockDataSchema, db: Session = Depends(database.get_db)):
    db_data = models.StockData(**data.model_dump())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.get("/strategy/performance")
def get_strategy_performance(db: Session = Depends(database.get_db)):
    data = db.query(models.StockData).order_by(models.StockData.datetime).all()
    if len(data) < 50:  # Minimum data points needed for the strategy
        raise HTTPException(status_code=400, detail="Not enough data points")
    return strategy.calculate_moving_averages(data) 