from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class Trade:
    def __init__(self,
                 entry_price: float,
                 size: float,
                 entry_time: Union[datetime, str],
                 side: str,
                 sl_price: float,
                 tp_price: float,
                 sl_monetary_value: float,
                 point_value: Optional[float] = None):
        """
        Initialize a trade with an initial position and stop-loss/take-profit.
        """
        self.side = side.lower()
        self.entry_time = pd.Timestamp(entry_time) if isinstance(entry_time, str) else entry_time
        self.initial_entry_price = entry_price
        self.avg_entry_price = entry_price
        self.initial_size = size
        self.current_size = size
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.exit_time: Optional[datetime] = None
        self.realized_profit = 0.0

        # Calculate point value if not provided.
        sl_distance = abs(entry_price - sl_price)
        if sl_distance == 0:
            raise ValueError("Stop-loss distance cannot be zero.")
        self.point_value = point_value or (abs(sl_monetary_value) / (sl_distance * size))
        if not (0 < self.point_value < 10_000):
            raise ValueError("Calculated point value is out of expected range.")

        self.modifications: List[Dict[str, Any]] = []
        self.modifications.append({
            'action': 'initial_trade',
            'time': self.entry_time,
            'entry_price': entry_price,
            'size': size,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'point_value': self.point_value,
            'side': self.side
        })

    def add_position(self,
                     entry_price: float,
                     size: float,
                     entry_time: Union[datetime, str],
                     sl_price: Optional[float] = None,
                     tp_price: Optional[float] = None) -> None:
        entry_time = pd.Timestamp(entry_time) if isinstance(entry_time, str) else entry_time
        total_cost = self.avg_entry_price * self.current_size + entry_price * size
        self.current_size += size
        self.avg_entry_price = total_cost / self.current_size

        if sl_price is not None:
            self.sl_price = sl_price
        if tp_price is not None:
            self.tp_price = tp_price

        self.modifications.append({
            'action': 'add_position',
            'time': entry_time,
            'entry_price': entry_price,
            'size': size,
            'new_sl': sl_price,
            'new_tp': tp_price
        })

    def close_position(self,
                       exit_price: float,
                       exit_time: Union[datetime, str],
                       size: Optional[float] = None) -> None:
        exit_time = pd.Timestamp(exit_time) if isinstance(exit_time, str) else exit_time
        size_to_close = size or self.current_size
        if size_to_close > self.current_size:
            raise ValueError("Cannot close more than the current position size.")
            
        profit = self._calc_profit(exit_price, size_to_close)
        self.realized_profit += profit
        self.current_size -= size_to_close

        action = 'close_trade' if self.current_size == 0 else 'partial_close'
        event = {
            'action': action,
            'time': exit_time,
            'exit_price': exit_price,
            'closed_size': size_to_close,
            'remaining_size': self.current_size,
            'profit': profit
        }
        self.modifications.append(event)

        if self.current_size == 0:
            self.exit_time = exit_time

    def modify_sl_tp(self,
                     modification_time: Union[datetime, str],
                     new_sl: Optional[float] = None,
                     new_tp: Optional[float] = None) -> None:
        mod_time = pd.Timestamp(modification_time) if isinstance(modification_time, str) else modification_time
        if new_sl is not None:
            self.sl_price = new_sl
        if new_tp is not None:
            self.tp_price = new_tp

        self.modifications.append({
            'action': 'modify_sl_tp',
            'time': mod_time,
            'new_sl': new_sl,
            'new_tp': new_tp
        })

    def _calc_profit(self, price: float, size: float) -> float:
        if self.side == 'long':
            return (price - self.avg_entry_price) * size * self.point_value
        else:  # short
            return (self.avg_entry_price - price) * size * self.point_value

    def get_trade_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            'side': self.side,
            'initial_entry_time': self.entry_time,
            'final_exit_time': self.exit_time,
            'duration_sec': (self.exit_time - self.entry_time).total_seconds() if self.exit_time else None,
            'initial_entry_price': self.initial_entry_price,
            'avg_entry_price': self.avg_entry_price,
            'current_size': self.current_size,
            'total_profit': self.realized_profit,
            'point_value': self.point_value,
            'sl_price': self.sl_price,
            'tp_price': self.tp_price,
            'n_modifications': len(self.modifications),
            'modifications': self.modifications
        }
        return summary

    def get_state_history(self) -> pd.DataFrame:
        state_history = []
        
        state = {
            'time': self.modifications[0]['time'],
            'action': self.modifications[0]['action'],
            'avg_entry_price': self.modifications[0]['entry_price'],
            'current_size': self.modifications[0]['size'],
            'realized_profit': 0.0,
            'sl_price': self.modifications[0]['sl_price'],
            'tp_price': self.modifications[0]['tp_price'],
            'point_value': self.modifications[0]['point_value']
        }
        if state['current_size'] > 0 and state['sl_price'] is not None:
            state['open_risk'] = abs(state['avg_entry_price'] - state['sl_price']) * state['current_size'] * state['point_value']
        else:
            state['open_risk'] = 0.0
            
        state_history.append(state.copy())
        
        for mod in self.modifications[1:]:
            new_state = state.copy()
            new_state['time'] = mod['time']
            new_state['action'] = mod['action']
            
            if mod['action'] == 'add_position':
                prev_size = new_state['current_size']
                add_size = mod['size']
                prev_avg = new_state['avg_entry_price']
                add_price = mod['entry_price']
                new_size = prev_size + add_size
                new_avg = (prev_avg * prev_size + add_price * add_size) / new_size
                new_state['avg_entry_price'] = new_avg
                new_state['current_size'] = new_size
                if mod.get('new_sl') is not None:
                    new_state['sl_price'] = mod['new_sl']
                if mod.get('new_tp') is not None:
                    new_state['tp_price'] = mod['new_tp']
            elif mod['action'] in ['partial_close', 'close_trade']:
                new_state['current_size'] -= mod['closed_size']
                new_state['realized_profit'] += mod['profit']
                if mod['action'] == 'close_trade':
                    new_state['current_size'] = 0
            elif mod['action'] == 'modify_sl_tp':
                if mod.get('new_sl') is not None:
                    new_state['sl_price'] = mod['new_sl']
                if mod.get('new_tp') is not None:
                    new_state['tp_price'] = mod['new_tp']
                    
            if new_state['current_size'] > 0 and new_state['sl_price'] is not None:
                new_state['open_risk'] = abs(new_state['avg_entry_price'] - new_state['sl_price']) * new_state['current_size'] * new_state['point_value']
            else:
                new_state['open_risk'] = 0.0
            state = new_state.copy()
            state_history.append(new_state.copy())
            
        df = pd.DataFrame(state_history)
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        return df

    def to_trade_row(self) -> Dict[str, Any]:
        summary = self.get_trade_summary()
        row = {
            'side': summary['side'],
            'initial_entry_time': summary['initial_entry_time'],
            'final_exit_time': summary['final_exit_time'],
            'duration_sec': summary['duration_sec'],
            'initial_entry_price': summary['initial_entry_price'],
            'avg_entry_price': summary['avg_entry_price'],
            'initial_size': self.initial_size,
            'final_size': summary['current_size'],
            'total_profit': summary['total_profit'],
            'point_value': summary['point_value'],
            'sl_price': summary['sl_price'],
            'tp_price': summary['tp_price'],
            'n_modifications': summary['n_modifications']
        }
        return row

    def plot_trade_levels(self) -> None:
        """
        Plots the trade levels over time using seaborn.
        This includes:
         - The evolving average entry price.
         - SL and TP levels.
         - The open risk at each event.
        """
        df = self.get_state_history()
        
        # Melt the DataFrame so that we can plot multiple lines easily.
        df_melted = df.melt(id_vars=["time", "action"], value_vars=["avg_entry_price", "sl_price", "tp_price", "open_risk"],
                            var_name="level_type", value_name="value")
        
        # Initialize the seaborn style.
        sns.set(style="whitegrid")
        
        plt.figure(figsize=(12, 6))
        ax = sns.lineplot(data=df_melted, x="time", y="value", hue="level_type", marker="o")
        
        # Annotate events on the plot (optionally, add action labels on top of the markers).
        for idx, row in df.iterrows():
            ax.annotate(row['action'], (row['time'], row['open_risk']), 
                        textcoords="offset points", xytext=(0, 5),
                        ha='center', fontsize=8, color="black")
        
        ax.set_title("Trade Price Levels & Open Risk Over Time")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.legend(title="Level")
        plt.show()

    def __repr__(self) -> str:
        """
        Provide a concise summary of the trade for debugging purposes.
        Example output:
          Trade(long): Entry=1.2000 at 2023-10-01 09:00:00, Avg=1.2010,
          Open Size=50, Profit=+150.00, SL=1.1950, TP=1.2100, Modifications=4
        """
        summary = self.get_trade_summary()
        status = "Closed" if self.exit_time is not None else "Open"
        profit_str = f"{summary['total_profit']:.2f}"
        return (f"Trade({self.side.title()}): Entry={summary['initial_entry_price']:.4f} @ {summary['initial_entry_time']}, "
                f"Avg={summary['avg_entry_price']:.4f}, Size={summary['current_size']}, Profit={profit_str}, "
                f"SL={summary['sl_price']:.4f}, TP={summary['tp_price']:.4f}, "
                f"Status={status}, Mods={summary['n_modifications']})")

    def __str__(self) -> str:
        summary = self.get_trade_summary()
        lines = [
            f"Trade Summary:",
            f"  Side: {summary['side']}",
            f"  Entry: {summary['initial_entry_price']} @ {summary['initial_entry_time']}",
            f"  Avg Entry: {summary['avg_entry_price']}",
            f"  Current Size: {summary['current_size']}",
            f"  SL: {summary['sl_price']}  TP: {summary['tp_price']}",
            f"  Total Profit: {summary['total_profit']:.2f}",
            f"  Point Value: {summary['point_value']}",
            f"  Duration (sec): {summary['duration_sec']}",
            f"  Modifications:"
        ]
        for mod in summary['modifications']:
            lines.append(f"    {mod['time']} - {mod['action']}: {mod}")
        return "\n".join(lines)

# --- Example usage in Jupyter Notebook ---
if __name__ == "__main__":
    # Create a trade instance.
    trade = Trade(entry_price=1.2000,
                  size=100,
                  entry_time="2023-10-01 09:00:00",
                  side="long",
                  sl_price=1.1950,
                  tp_price=1.2100,
                  sl_monetary_value=500)
    trade.add_position(entry_price=1.2010,
                       size=50,
                       entry_time="2023-10-01 09:30:00")
    trade.modify_sl_tp(modification_time="2023-10-01 10:00:00", new_sl=1.1940)
    trade.close_position(exit_price=1.2050, exit_time="2023-10-01 11:00:00", size=80)
    trade.close_position(exit_price=1.2080, exit_time="2023-10-01 12:00:00")
    
    # Print the concise representation.
    print(repr(trade))
    
    # Plot the trade levels and open risk over time using seaborn.
    trade.plot_trade_levels()
