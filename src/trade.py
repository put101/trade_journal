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
        Initialize a trade with an initial position, stop-loss, and take-profit.
        The stop loss is specified as a price but stored as a distance from entry.
        """
        self.side = side.lower()
        self.entry_time = pd.Timestamp(entry_time) if isinstance(entry_time, str) else entry_time
        self.initial_entry_price = entry_price
        self.avg_entry_price = entry_price
        self.initial_size = size
        self.current_size = size
        
        # Calculate initial stop loss distance
        self.initial_sl_distance = abs(entry_price - sl_price)
        if self.initial_sl_distance == 0:
            raise ValueError("Stop-loss distance cannot be zero.")
            
        # Current SL and TP prices (can be modified)
        self.sl_price = sl_price
        self.tp_price = tp_price
        
        self.exit_time: Optional[datetime] = None
        self.realized_profit = 0.0

        # Calculate point value if not provided
        self.point_value = point_value or (abs(sl_monetary_value) / (self.initial_sl_distance * size))
        if not (0 < self.point_value < 10_000):
            raise ValueError("Calculated point value is out of expected range.")

        # Flags and counters for partial closes
        self.has_partials_closed = False
        self.n_partial_closes = 0
        self.first_partial_close_time: Optional[datetime] = None
        self.last_partial_close_time: Optional[datetime] = None

        # Event log
        self.modifications: List[Dict[str, Any]] = []
        self.modifications.append({
            'action': 'initial_trade',
            'time': self.entry_time,
            'entry_price': entry_price,
            'size': size,
            'initial_sl_distance': self.initial_sl_distance,
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
                       size: Optional[float] = None,
                       close_reason: Optional[str] = None) -> None:
        """
        Close part or all of the trade.
        
        The optional close_reason parameter lets the user indicate why the trade was closed (e.g. "SL", "TP", "BE", "Manual").
        """
        exit_time = pd.Timestamp(exit_time) if isinstance(exit_time, str) else exit_time
        size_to_close = size or self.current_size
        if size_to_close > self.current_size:
            raise ValueError("Cannot close more than the current position size.")
            
        profit = self._calc_profit(exit_price, size_to_close)
        self.realized_profit += profit
        self.current_size -= size_to_close

        # Check and update partial close flags.
        if size_to_close < (self.current_size + size_to_close):
            self.has_partials_closed = True
            self.n_partial_closes += 1
            if self.first_partial_close_time is None:
                self.first_partial_close_time = exit_time
            self.last_partial_close_time = exit_time

        action = 'close_trade' if self.current_size == 0 else 'partial_close'
        event = {
            'action': action,
            'time': exit_time,
            'exit_price': exit_price,
            'closed_size': size_to_close,
            'remaining_size': self.current_size,
            'profit': profit,
            'close_reason': close_reason
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

    def potential_profit(self) -> float:
        """
        Compute the potential profit if the TP level is hit.
        """
        if self.current_size <= 0:
            return 0.0
        if self.side == 'long':
            return (self.tp_price - self.avg_entry_price) * self.current_size * self.point_value
        else:
            return (self.avg_entry_price - self.tp_price) * self.current_size * self.point_value

    def potential_loss(self) -> float:
        """
        Compute the potential loss if the SL level is hit.
        """
        if self.current_size <= 0:
            return 0.0
        if self.side == 'long':
            return (self.avg_entry_price - self.sl_price) * self.current_size * self.point_value
        else:
            return (self.sl_price - self.avg_entry_price) * self.current_size * self.point_value

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
            'initial_sl_distance': self.initial_sl_distance,
            'sl_price': self.sl_price,
            'tp_price': self.tp_price,
            'n_modifications': len(self.modifications),
            'potential_profit': self.potential_profit(),
            'potential_loss': self.potential_loss(),
            'has_partials_closed': self.has_partials_closed,
            'n_partial_closes': self.n_partial_closes,
            'first_partial_close_time': self.first_partial_close_time,
            'last_partial_close_time': self.last_partial_close_time,
            'modifications': self.modifications
        }
        return summary

    def get_state_history(self) -> pd.DataFrame:
        """
        Replay the events logged in modifications to generate a state history DataFrame.
        Each row includes the evolving average entry price, SL, TP, open risk,
        and now also potential profit and loss.
        """
        state_history = []
        
        # Define a helper to compute potential profit and loss for a given state.
        def compute_pros(state):
            if state['current_size'] > 0:
                if self.side == 'long':
                    state['potential_profit'] = (state['tp_price'] - state['avg_entry_price']) * state['current_size'] * state['point_value']
                    state['potential_loss'] = (state['avg_entry_price'] - state['sl_price']) * state['current_size'] * state['point_value']
                else:
                    state['potential_profit'] = (state['avg_entry_price'] - state['tp_price']) * state['current_size'] * state['point_value']
                    state['potential_loss'] = (state['sl_price'] - state['avg_entry_price']) * state['current_size'] * state['point_value']
            else:
                state['potential_profit'] = 0.0
                state['potential_loss'] = 0.0

        # Build initial state.
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
        state['open_risk'] = (abs(state['avg_entry_price'] - state['sl_price']) *
                              state['current_size'] * state['point_value']) if state['current_size'] > 0 else 0.0
        compute_pros(state)
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
                    
            new_state['open_risk'] = (abs(new_state['avg_entry_price'] - new_state['sl_price']) *
                                       new_state['current_size'] * new_state['point_value']) if new_state['current_size'] > 0 else 0.0
            compute_pros(new_state)
            state = new_state.copy()
            state_history.append(new_state.copy())
            
        df = pd.DataFrame(state_history)
        df['time'] = pd.to_datetime(df['time'])
        return df.sort_values('time').reset_index(drop=True)

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
            'initial_sl_distance': self.initial_sl_distance,
            'sl_price': summary['sl_price'],
            'tp_price': summary['tp_price'],
            'n_modifications': summary['n_modifications'],
            'potential_profit': summary['potential_profit'],
            'potential_loss': summary['potential_loss'],
            'has_partials_closed': summary['has_partials_closed'],
            'n_partial_closes': summary['n_partial_closes']
        }
        return row

    def plot_trade_levels(self) -> None:
        """
        Plot the evolution of trade levels over time using seaborn.
        This includes:
          - Average entry price, SL, TP on the primary y-axis
          - Open risk, potential profit and potential loss on the secondary y-axis
        """
        df = self.get_state_history()
        
        # Separate price and risk columns
        price_columns = ["avg_entry_price", "sl_price", "tp_price"]
        risk_columns = ["open_risk", "potential_profit", "potential_loss"]
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax2 = ax1.twinx()
        
        # Plot price data on primary y-axis
        df_prices = df.melt(id_vars=["time", "action"], value_vars=price_columns,
                           var_name="level_type", value_name="value")
        sns.lineplot(data=df_prices, x="time", y="value", hue="level_type", 
                    marker="o", ax=ax1, linestyle='-')
        
        # Plot risk data on secondary y-axis
        df_risks = df.melt(id_vars=["time", "action"], value_vars=risk_columns,
                          var_name="level_type", value_name="value")
        sns.lineplot(data=df_risks, x="time", y="value", hue="level_type",
                    marker="s", ax=ax2, linestyle='--')
        
        # Add initial SL distance annotation
        ax1.axhspan(self.initial_entry_price - self.initial_sl_distance, 
                   self.initial_entry_price + self.initial_sl_distance,
                   alpha=0.1, color='red', label='Initial SL Range')
        
        # Annotate events on the plot
        for _, row in df.iterrows():
            ax1.annotate(row['action'], (row['time'], row['avg_entry_price']),
                        textcoords="offset points", xytext=(0, 10),
                        ha='center', fontsize=8, color="black")
        
        # Customize the plot
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Price")
        ax2.set_ylabel("Risk/P&L")
        
        # Adjust legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1, labels1, loc='upper left', title="Price Levels")
        ax2.legend(lines2, labels2, loc='upper right', title="Risk Metrics")
        
        plt.title("Trade Levels Over Time")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def __repr__(self) -> str:
        """
        A concise representation for debugging.
        Example:
          Trade(Long): Entry=1.2000 @ 2023-10-01 09:00:00, Avg=1.2010, Size=50, Profit=+150.00,
                      SL=1.1950, TP=1.2100, Status=Closed, Mods=4
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
            "Trade Summary:",
            f"  Side: {summary['side']}",
            f"  Entry: {summary['initial_entry_price']} @ {summary['initial_entry_time']}",
            f"  Avg Entry: {summary['avg_entry_price']}",
            f"  Current Size: {summary['current_size']}",
            f"  SL: {summary['sl_price']}  TP: {summary['tp_price']}",
            f"  Total Profit: {summary['total_profit']:.2f}",
            f"  Point Value: {summary['point_value']}",
            f"  Duration (sec): {summary['duration_sec']}",
            f"  Potential Profit: {summary['potential_profit']:.2f}",
            f"  Potential Loss: {summary['potential_loss']:.2f}",
            f"  Partials Closed: {summary['has_partials_closed']} (n={summary['n_partial_closes']})",
            "  Modifications:"
        ]
        for mod in summary['modifications']:
            lines.append(f"    {mod['time']} - {mod['action']}: {mod}")
        return "\n".join(lines)

# --- Example usage in your Jupyter Notebook ---
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
    # Partial close with reason.
    trade.close_position(exit_price=1.2050, exit_time="2023-10-01 11:00:00", size=80, close_reason="Partial Close")
    # Final close with reason.
    trade.close_position(exit_price=1.2080, exit_time="2023-10-01 12:00:00", close_reason="TP Hit")
    
    # Print concise representation.
    print(repr(trade))
    
    # Plot the trade evolution including potential profit/loss.
    trade.plot_trade_levels()
    
    # Convert trade into one row for DataFrame aggregation.
    trade_row = trade.to_trade_row()
    df = pd.DataFrame([trade_row])
    print(df)
