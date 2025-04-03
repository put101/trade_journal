from datetime import datetime
from typing import Optional, Dict, List, Union
from enum import StrEnum
import pprint
import pandas as pd

""" 
- Designed for retrospective journaling of trades with full lifecycle tracking
- Models real-world broker position management (e.g. cTrader) using average pricing
- Tracks multiple entries and partial exits using FIFO logic, maintaining state granularity
- Stores side (long/short), SL/TP, entry/exit times, and dynamic point value per trade
- Computes real-time and historical metrics like avg entry, monetary risk, and PnL potential
- Enables quality-of-life helpers for dynamic SL recalculation, breakeven, and forward profit planning
- Preserves a rich modification history with timestamped actions for replay and plotting
- Optimized for analysis, visualization, and risk review workflows during and after trades
"""

__ALL__ = []

CONST_BUY = "buy"
CONST_SELL = "sell"

__ALL__ += [CONST_BUY, CONST_SELL]

# Position keys
KEY_entry_price = "entry_price"
KEY_exit_price = "exit_price"
KEY_entry_time = "entry_time"
KEY_side = "side"
KEY_exit_time = "exit_time"
KEY_closed = 'closed'
KEY_size = 'size'
KEY_point_value = 'point_value'
__ALL__.extend([KEY_entry_price, KEY_exit_price, KEY_entry_time, 
                KEY_side, KEY_exit_time, KEY_closed, KEY_size, KEY_point_value])

# Trade keys
KEY_sl_price = 'sl_price'
KEY_tp_price = 'tp_price'
__ALL__ += [KEY_sl_price, KEY_tp_price]

# Modifications keys
KEY_action = 'action'
KEY_time = 'time'
KEY_closed_size = 'closed_size'
KEY_remaining_size= 'remaining_size'
KEY_new_tp = 'new_tp'
KEY_new_sl = 'new_sl'
__ALL__.extend([KEY_action, KEY_time, KEY_closed_size, KEY_remaining_size, KEY_new_sl, KEY_new_tp])

KEY_avg_entry_price = 'avg_entry_price'
KEY_total_size= 'total_size'
KEY_positions= 'positions'
KEY_n_positions= 'n_positions'
KEY_modifications= 'modifications'
__ALL__.extend([KEY_avg_entry_price, KEY_total_size, KEY_positions, KEY_n_positions, KEY_modifications])

class Position:
    def __init__(self, entry_price: float, size: float, entry_time: Union[datetime, str], point_value: float, side: str):
        # Dynamic conversion: if entry_time is a string, convert to Timestamp
        if isinstance(entry_time, str):
            entry_time = pd.Timestamp(entry_time)
        self.entry_price = entry_price
        self.size = size
        self.entry_time = entry_time
        self.point_value = point_value
        self.side = side
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None

    def close(self, exit_price: float, exit_time: Union[datetime, str]):
        # Convert exit_time if needed
        if isinstance(exit_time, str):
            exit_time = pd.Timestamp(exit_time)
        self.exit_price = exit_price
        self.exit_time = exit_time

    def is_closed(self):
        return self.exit_price is not None

    def risk_at_price(self, price: float) -> dict:
        risk = abs(self.entry_price - price) * self.size * self.point_value
        return risk 

    def to_dict(self) -> Dict: 
        return {
            KEY_entry_price: self.entry_price,
            KEY_size: self.size,
            KEY_entry_time: self.entry_time,
            KEY_side: self.side,
            KEY_exit_price: self.exit_price,
            KEY_exit_time: self.exit_time,
            KEY_closed: self.is_closed(),
            KEY_point_value: self.point_value,
        }

class Execution:
    def __init__(self, entry_price: float, entry_time: Union[datetime, str], sl_price: float, tp_price: float,
                 size: float, side: str, sl_monetary_value: float, point_value: Optional[float] = None):
        # Dynamic conversion: if entry_time is a string, convert to Timestamp
        if isinstance(entry_time, str):
            entry_time = pd.Timestamp(entry_time)
            
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.side = side  # long or short
        self.positions: List[Position] = []
        self.modifications: List[Dict[str, any]] = []

        sl_distance = abs(entry_price - sl_price)
        if sl_distance == 0:
            raise ValueError("Stop-loss distance cannot be zero.")
        
        if point_value is None:
            self.point_value = Execution.calc_point_value(sl_monetary_value, sl_distance, size)
        else:
            self.point_value = point_value

        assert 10_000 > self.point_value > 0         

        initial_position = Position(entry_price, size, entry_time, self.point_value, side)
        self.positions.append(initial_position)

        self.modifications.append({
            KEY_action: "initial_position",
            KEY_time: entry_time,
            KEY_entry_price: entry_price,
            KEY_size: size,
            KEY_sl_price: sl_price,
            KEY_tp_price: tp_price,
            KEY_point_value: self.point_value,
            KEY_side: side
        })
        
    def __repr__(self) -> str:
        d = self.get_trade_summary()
        return pprint.pformat(d)
    
    def __str__(self) -> str:
        return self.get_trade_summary()

    @classmethod
    def calc_point_value(cls, sl_monetary_value, sl_distance, size):
        return abs(sl_monetary_value) / (sl_distance * size)
    
    def get_sl_for_risk(self, target_risk: float) -> float:
        avg_price = self.avg_entry_price
        if self.side == 'long':
            return avg_price - (target_risk / (self.total_size * self.point_value))
        else:
            return avg_price + (target_risk / (self.total_size * self.point_value))

    def potential_profit_at_price(self, target_price: float) -> float:
        profit = (target_price - self.avg_entry_price) if self.side == 'long' else (self.avg_entry_price - target_price)
        return profit * self.total_size * self.point_value

    def breakeven_price(self) -> float:
        return self.avg_entry_price

    @property
    def total_size(self):
        return sum(p.size for p in self.positions if not p.is_closed())

    @property
    def avg_entry_price(self):
        open_positions = [p for p in self.positions if not p.is_closed()]
        total_value = sum(p.entry_price * p.size for p in open_positions)
        total_size = sum(p.size for p in open_positions)
        return total_value / total_size if total_size else None

    def avg_risk_at_price(self, price: float) -> float:
        open_positions = [p for p in self.positions if not p.is_closed()]
        if not open_positions:
            return 0.0
        total_risk = sum(p.risk_at_price(price) for p in open_positions)
        return total_risk / len(open_positions)

    def add_position(self, entry_price: float, size: float, entry_time: Union[datetime, str]):
        # Convert entry_time if it is a string
        if isinstance(entry_time, str):
            entry_time = pd.Timestamp(entry_time)
        position = Position(entry_price, size, entry_time, self.point_value, self.side)
        self.positions.append(position)
        self.modifications.append({
            KEY_action: "add_position",
            KEY_time: entry_time,
            KEY_entry_price: entry_price,
            KEY_size: size
        })

    def close_position_fifo(self, size: float, exit_price: float, exit_time: Union[datetime, str]):
        # Convert exit_time if it is a string
        if isinstance(exit_time, str):
            exit_time = pd.Timestamp(exit_time)
        remaining_size = size

        for position in self.positions:
            if position.is_closed():
                continue

            if position.size <= remaining_size:
                remaining_size -= position.size
                position.close(exit_price, exit_time)
                self.modifications.append({
                    KEY_action: "close_position",
                    KEY_time: exit_time,
                    KEY_exit_price: exit_price,
                    KEY_closed_size: position.size
                })
            else:
                closed_position = Position(position.entry_price, remaining_size, position.entry_time, self.point_value, self.side)
                closed_position.close(exit_price, exit_time)
                self.positions.append(closed_position)

                position.size -= remaining_size
                self.modifications.append({
                    KEY_action: "partial_close",
                    KEY_time: exit_time,
                    KEY_exit_price: exit_price,
                    KEY_remaining_size: remaining_size
                })
                remaining_size = 0

            if remaining_size == 0:
                break

        if remaining_size > 0:
            raise Exception("Attempted to close more than the total open size.")

    def modify_sl_tp(self, modification_time: Union[datetime, str], new_sl: Optional[float] = None, new_tp: Optional[float] = None):
        # Convert modification_time if it is a string
        if isinstance(modification_time, str):
            modification_time = pd.Timestamp(modification_time)
        if new_sl is not None:
            self.sl_price = new_sl
        if new_tp is not None:
            self.tp_price = new_tp

        self.modifications.append({
            KEY_action: "modify_sl_tp",
            KEY_time: modification_time,
            KEY_new_sl: new_sl,
            KEY_new_tp: new_tp
        })

    def get_trade_summary(self) -> dict:
        positions_summary: List[dict] = [p.to_dict() for p in self.positions]
        
        return {
            KEY_avg_entry_price: self.avg_entry_price,
            KEY_total_size: self.total_size,
            KEY_sl_price: self.sl_price,
            KEY_tp_price: self.tp_price,
            KEY_positions: positions_summary,
            KEY_n_positions: len(self.positions),
            KEY_modifications: self.modifications,
            KEY_side: self.side
        }

    def print_modifications(self):
        for mod in self.modifications:
            print(f"{mod['time']} - {mod['action']}: {mod}")

__ALL__ = __ALL__.extend([Execution, Position])


assert type(CONST_BUY)==str
assert CONST_BUY == 'buy'
