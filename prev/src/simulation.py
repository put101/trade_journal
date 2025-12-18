from dataclasses import dataclass
from datetime import datetime, time, timedelta
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict
from src.journal import Execution, TradePosition, EntryTime, RR, Outcome, MultiTimeframeAnalysis, Confidence, RiskManagement, Account
import random
import scipy.stats
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class TradingSession:
    name: str
    start_time: time
    end_time: time
    
    def is_within_session(self, dt: datetime) -> bool:
        return self.start_time <= dt.time() <= self.end_time

    @classmethod
    def london_session(cls):
        return cls("London", time(8, 0), time(16, 30))

    @classmethod
    def ny_session(cls):
        return cls("New York", time(13, 30), time(20, 0))

    @classmethod
    def asian_session(cls):
        return cls("Asia", time(0, 0), time(8, 0))

@dataclass
class SimConfig:
    total_trades: int
    max_trades_per_day: int
    trade_probability_per_hour: float
    trading_sessions: List[TradingSession]
    rr_range: Tuple[float, float]  # min, max RR
    win_rate: float
    sl_points: float = 0.0050  # Default 50 pip stop loss
    account_name: str = "sim_account"
    start_date: datetime = datetime.now() - timedelta(days=90)
    end_date: datetime = datetime.now()

    @classmethod
    def create_default(cls) -> 'SimConfig':
        return cls(
            total_trades=100,
            max_trades_per_day=3,
            trade_probability_per_hour=0.3,
            trading_sessions=[TradingSession.london_session(), TradingSession.ny_session()],
            rr_range=(1.5, 3.0),
            win_rate=0.55
        )

    @classmethod
    def create_conservative(cls) -> 'SimConfig':
        return cls(
            total_trades=50,
            max_trades_per_day=2,
            trade_probability_per_hour=0.2,
            trading_sessions=[TradingSession.london_session()],
            rr_range=(1.0, 2.0),
            win_rate=0.65,
            sl_points=0.0030
        )

    @classmethod
    def create_aggressive(cls) -> 'SimConfig':
        return cls(
            total_trades=200,
            max_trades_per_day=5,
            trade_probability_per_hour=0.4,
            trading_sessions=[TradingSession.london_session(), TradingSession.ny_session(), TradingSession.asian_session()],
            rr_range=(2.0, 5.0),
            win_rate=0.45,
            sl_points=0.0080
        )

def generate_simulated_trades(config: SimConfig) -> List[Execution]:
    """Generate simulated trades based on configuration"""
    trades = []
    current_date = config.start_date
    trade_count = 0
    
    while trade_count < config.total_trades and current_date <= config.end_date:
        if current_date.weekday() < 5:  # Only trade on weekdays
            daily_trades = 0
            
            for hour in range(24):
                dt = current_date.replace(hour=hour)
                
                # Check if time is within any trading session
                in_session = any(session.is_within_session(dt) for session in config.trading_sessions)
                
                if in_session and daily_trades < config.max_trades_per_day:
                    if random.random() < config.trade_probability_per_hour:
                        # Create trade
                        trade = Execution(uid=f"sim_{trade_count}")
                        
                        # Add account
                        Account.add_to_trade(trade, config.account_name)
                        
                        # Generate trade parameters
                        is_long = random.choice([True, False])
                        rr = random.uniform(config.rr_range[0], config.rr_range[1])
                        is_win = random.random() < config.win_rate
                        
                        # Generate prices
                        entry_price = 1.1000 + random.uniform(-0.0100, 0.0100)
                        sl_points = config.sl_points
                        
                        if is_long:
                            sl_price = entry_price - sl_points
                            tp_price = entry_price + (sl_points * rr)
                            close_price = tp_price if is_win else sl_price
                        else:
                            sl_price = entry_price + sl_points
                            tp_price = entry_price - (sl_points * rr)
                            close_price = tp_price if is_win else sl_price
                        
                        # Create position
                        position = TradePosition(
                            entry_price=round(entry_price, 4),
                            sl_price=round(sl_price, 4),
                            tp_price=round(tp_price, 4),
                            close_price=round(close_price, 4)
                        )
                        position.add_tags_to_trade(trade)
                        
                        # Add random minutes to the hour
                        minutes = random.randint(0, 59)
                        entry_time = dt.replace(minute=minutes)
                        EntryTime(entry_time=entry_time).add_tags_to_trade(trade)
                        
                        # Add other metadata
                        RR.add_tags_to_trade(trade)
                        Outcome.add_tags_to_trade(trade)
                        MultiTimeframeAnalysis.add_tags_to_trade(trade, random.choice([True, False]))
                        Confidence.add_tags_to_trade(trade, random.randint(1, 5))
                        RiskManagement.add_tags_to_trade(trade, random.choice([
                            RiskManagement.NO_MANAGEMENT,
                            RiskManagement.BE_AFTER_1R,
                            RiskManagement.BE_AFTER_PUSH,
                            RiskManagement.CLOSE_EARLY
                        ]))
                        
                        trades.append(trade)
                        trade_count += 1
                        daily_trades += 1
                        
                        if trade_count >= config.total_trades:
                            break
                            
            current_date += timedelta(days=1)
    
    return trades

def analyze_simulation(trades: List[Execution]) -> Dict:
    """Analyze simulation results"""
    data = []
    for trade in trades:
        data.append({
            'entry_time': trade.get_entry_time(),
            'return_points': trade.get_return_points(),
            'rr': trade.get_rr(),
            'is_win': trade.is_win()
        })
    
    df = pd.DataFrame(data)
    df.sort_values('entry_time', inplace=True)
    df['cumulative_return'] = df['return_points'].cumsum()
    df['drawdown'] = df['cumulative_return'] - df['cumulative_return'].cummax()
    
    return {
        'total_trades': len(trades),
        'win_rate': df['is_win'].mean(),
        'avg_winner': df[df['is_win']]['return_points'].mean(),
        'avg_loser': df[~df['is_win']]['return_points'].mean(),
        'profit_factor': abs(df[df['return_points'] > 0]['return_points'].sum() / 
                           df[df['return_points'] < 0]['return_points'].sum()),
        'max_drawdown': df['drawdown'].min(),
        'final_return': df['return_points'].sum(),
        'avg_rr': df['rr'].mean(),
        'df': df  # Return DataFrame for plotting
    }

def plot_simulation_results(trades: List[Execution], title: str = "Simulation Results"):
    """Plot simulation results"""
    analysis = analyze_simulation(trades)
    df = analysis['df']
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # Equity curve
    ax1.plot(df['entry_time'], df['cumulative_return'], label='Equity Curve')
    ax1.set_title(f'{title} - Equity Curve')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Return (points)')
    ax1.grid(True)
    
    # Add key metrics as text
    metrics_text = (
        f"Total Trades: {analysis['total_trades']}\n"
        f"Win Rate: {analysis['win_rate']:.1%}\n"
        f"Profit Factor: {analysis['profit_factor']:.2f}\n"
        f"Max DD: {analysis['max_drawdown']:.4f}\n"
        f"Final Return: {analysis['final_return']:.4f}"
    )
    ax1.text(0.02, 0.98, metrics_text,
             transform=ax1.transAxes,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Drawdown
    ax2.fill_between(df['entry_time'], df['drawdown'], 0, color='red', alpha=0.3)
    ax2.set_title('Drawdown')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown (points)')
    ax2.grid(True)
    
    plt.tight_layout()
    return fig

def run_simulation(config: Optional[SimConfig] = None) -> Tuple[List[Execution], Dict]:
    """
    Run a simulation and return both trades and analysis
    
    Example usage:
    # Run with default config
    trades, analysis = run_simulation()
    
    # Run with custom config
    config = SimConfig.create_conservative()
    trades, analysis = run_simulation(config)
    
    # Plot results
    plot_simulation_results(trades, "Conservative Strategy")
    """
    if config is None:
        config = SimConfig.create_default()
    
    trades = generate_simulated_trades(config)
    analysis = analyze_simulation(trades)
    
    return trades, analysis 