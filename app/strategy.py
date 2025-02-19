import pandas as pd
import numpy as np
from typing import List
from .models import StockData

def calculate_moving_averages(data: List[StockData], short_window: int = 20, long_window: int = 50):
    df = pd.DataFrame([{
        'datetime': record.datetime,
        'close': record.close
    } for record in data])
    
    df.set_index('datetime', inplace=True)
    df['SMA_short'] = df['close'].rolling(window=short_window).mean()
    df['SMA_long'] = df['close'].rolling(window=long_window).mean()
    
    # Generate signals
    df['signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1
    df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
    
    # Handle NaN values
    strategy_returns = df['strategy_returns'].fillna(0)
    total_returns = float(strategy_returns.sum())
    sharpe_ratio = float(strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)) if len(strategy_returns) > 1 else 0.0
    
    return {
        'total_returns': total_returns,
        'sharpe_ratio': sharpe_ratio if not np.isnan(sharpe_ratio) else 0.0,
        'number_of_trades': int(np.abs(df['signal'].diff().fillna(0)).sum() / 2)
    } 