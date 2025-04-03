from datetime import datetime
from statemachine import StateMachine, State

# Minimal PositionAction definition
class PositionAction:
    MARKET_ENTRY = "market_entry"
    LIMIT_ENTRY = "limit_entry"
    STOP_ENTRY = "stop_entry"
    MODIFY_POSITION = "modify_position"
    CLOSE_POSITION = "close_position"
    
    def __init__(self, action_type: str, ts: datetime):
        self.action_type = action_type
        self.ts = ts

# cTraderStylePosition using the official statemachine package and its plotting
class cTraderStylePosition(StateMachine):
    # Define states
    initial_state = State('initial', initial=True)
    active_state = State('active')
    modified_state = State('modified')
    closed_state = State('closed')
    tp_hit_state = State('tp_hit')
    sl_hit_state = State('sl_hit')
    
    # Define transitions (any entry moves from initial to active, modifications transition to modified, close from active/modified)
    enter_market = initial_state.to(active_state)
    modify = active_state.to(modified_state) | modified_state.to(modified_state)
    close = active_state.to(closed_state) | modified_state.to(closed_state)
    tp_hit = active_state.to(tp_hit_state) | modified_state.to(tp_hit_state)
    sl_hit = active_state.to(sl_hit_state) | modified_state.to(sl_hit_state)
    
    def __init__(self, point_value: float = 1):
        super().__init__()
        self.point_value = point_value
        self.actions = []
        self.state_history = []
        self.lot_size = 0
        self.avg_entry_price = 0
        self.sl_price = None
        self.tp_price = None
        self.avg_close_price = None
        self.side = None
        self.closed = False

    # Log the state (with current state id from the official package)
    def update_state(self, ts: datetime, price: float):
        state = {
            "timestamp": ts,
            "price": price,
            "lot_size": self.lot_size,
            "avg_entry_price": self.avg_entry_price,
            "pnl": self.compute_pnl(price),
            "open_risk": self.compute_open_risk() if self.sl_price is not None else None,
            "state": self.current_state.id,
        }
        self.state_history.append(state)
       
    def compute_pnl(self, price: float) -> float:
        if self.side == "long":
            return (price - self.avg_entry_price) * self.lot_size * self.point_value
        elif self.side == "short":
            return (self.avg_entry_price - price) * self.lot_size * self.point_value
        return 0

    def compute_open_risk(self) -> float:
        if self.sl_price is None:
            return None
        if self.side == "long":
            return (self.avg_entry_price - self.sl_price) * self.lot_size * self.point_value
        elif self.side == "short":
            return (self.sl_price - self.avg_entry_price) * self.lot_size * self.point_value
        return None

    # Entry actions trigger the "enter_market" transition
    def market_entry(self, lot_size: float, price: float, time: datetime, side: str, sl_price: float = None, tp_price: float = None):
        self.enter_market()  # trigger state transition
        self.lot_size = lot_size
        self.avg_entry_price = price
        self.side = side
        if sl_price is not None:
            self.sl_price = sl_price
        if tp_price is not None:
            self.tp_price = tp_price
        self.actions.append(PositionAction(PositionAction.MARKET_ENTRY, time))
        self.update_state(time, price)
       
    def limit_entry(self, lot_size: float, limit_price: float, filled_price: float, time: datetime, side: str, sl_price: float = None, tp_price: float = None):
        self.enter_market()  # same as market entry
        self.lot_size = lot_size
        self.avg_entry_price = filled_price
        self.side = side
        if sl_price is not None:
            self.sl_price = sl_price
        if tp_price is not None:
            self.tp_price = tp_price
        self.actions.append(PositionAction(PositionAction.LIMIT_ENTRY, time))
        self.update_state(time, filled_price)
        
    def stop_entry(self, lot_size: float, stop_price: float, filled_price: float, time: datetime, side: str, sl_price: float = None, tp_price: float = None):
        self.enter_market()  # same
        self.lot_size = lot_size
        self.avg_entry_price = filled_price
        self.side = side
        if sl_price is not None:
            self.sl_price = sl_price
        if tp_price is not None:
            self.tp_price = tp_price
        self.actions.append(PositionAction(PositionAction.STOP_ENTRY, time))
        self.update_state(time, filled_price)

    # Modification triggers a "modify" transition
    def modify_position(self, lot_size_change: float, price: float, time: datetime):
        self.modify()  # trigger state transition
        if lot_size_change > 0:
            new_total = self.lot_size + lot_size_change
            self.avg_entry_price = (self.lot_size * self.avg_entry_price + lot_size_change * price) / new_total
            self.lot_size = new_total
        else:
            self.lot_size += lot_size_change
        self.actions.append(PositionAction(PositionAction.MODIFY_POSITION, time))
        self.update_state(time, price)
        
    # Closing triggers the "close" transition
    def close_position(self, price: float, time: datetime):
        self.close()  # trigger state transition
        self.avg_close_price = price
        self.actions.append(PositionAction(PositionAction.CLOSE_POSITION, time))
        self.update_state(time, price)
        self.closed = True
        
    # Allows querying the state at any arbitrary timestamp (using current position parameters and a supplied price)
    def get_state_at(self, ts: datetime, price: float):
        return {
            "timestamp": ts,
            "price": price,
            "lot_size": self.lot_size,
            "avg_entry_price": self.avg_entry_price,
            "pnl": self.compute_pnl(price),
            "open_risk": self.compute_open_risk() if self.sl_price is not None else None,
            "state": self.current_state.id,
            "action": "query",
        }
    
    # Returns aggregated trade features that remain invariant throughout the position's life
    def get_aggregated_tags(self):
        tags = {
            "entry_price": self.avg_entry_price,
            "sl_price": self.sl_price,
            "tp_price": self.tp_price,
            "side": self.side,
            "final_pnl": self.compute_pnl(self.avg_close_price) if self.closed else self.compute_pnl(self.state_history[-1]['price']),
        }
        return tags
    
    # Remove the plot_state_machine method to disable graph plotting
    # def plot_state_machine(self, filename="state_machine.png", prog="dot"):
    #     try:
    #         graph = self.graph
    #         graph.draw(filename, prog=prog)
    #         print(f"State machine diagram saved as {filename}")
    #     except Exception as e:
    #         print("Plotting not available:", e) 

    def tp_hit_position(self, price: float, time: datetime):
        self.tp_hit()  # trigger state transition
        self.avg_close_price = price
        self.actions.append(PositionAction('tp_hit', time))
        self.update_state(time, price)
        self.closed = True

    def sl_hit_position(self, price: float, time: datetime):
        self.sl_hit()  # trigger state transition
        self.avg_close_price = price
        self.actions.append(PositionAction('sl_hit', time))
        self.update_state(time, price)
        self.closed = True 