from typing import Optional, Union, Dict, List
from datetime import datetime
import pandas as pd
from .trade import Position, KEY_action, KEY_time, KEY_entry_price, KEY_size, KEY_point_value, KEY_side, KEY_exit_price, KEY_closed_size, KEY_new_sl, KEY_new_tp

class PositionWrapper:
    """A wrapper around Position that tracks SL/TP/BE hits."""
    
    def __init__(self, position: Position):
        """Initialize the wrapper with a Position instance.
        
        Args:
            position: The Position instance to wrap
        """
        self.position = position
        self.sl_hit: Optional[datetime] = None
        self.tp_hit: Optional[datetime] = None
        self.be_hit: Optional[datetime] = None
        self._track_hits()
        
    def _track_hits(self) -> None:
        """Track SL/TP/BE hits from the position's history."""
        if not self.position.is_closed():
            return
            
        exit_price = self.position.exit_price
        entry_price = self.position.entry_price
        
        # Check if exit was due to SL/TP/BE
        if self.position.sl_price is not None and abs(exit_price - self.position.sl_price) < 1e-5:
            self.sl_hit = self.position.exit_time
        elif self.position.tp_price is not None and abs(exit_price - self.position.tp_price) < 1e-5:
            self.tp_hit = self.position.exit_time
        elif abs(exit_price - entry_price) < 1e-5:
            self.be_hit = self.position.exit_time
            
    def get_hit_info(self) -> Dict[str, Optional[datetime]]:
        """Get information about SL/TP/BE hits.
        
        Returns:
            Dictionary with keys 'sl_hit', 'tp_hit', 'be_hit' and their respective hit times
        """
        return {
            'sl_hit': self.sl_hit,
            'tp_hit': self.tp_hit,
            'be_hit': self.be_hit
        }
        
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped position."""
        return getattr(self.position, name)
        
    def __str__(self) -> str:
        """String representation including hit information."""
        base_str = str(self.position)
        hit_info = self.get_hit_info()
        hit_lines = []
        
        for hit_type, hit_time in hit_info.items():
            if hit_time is not None:
                hit_lines.append(f"  {hit_type}: {hit_time}")
                
        if hit_lines:
            base_str += "\nHit Information:"
            base_str += "\n" + "\n".join(hit_lines)
            
        return base_str 