from datetime import datetime
import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import scipy.stats
from src.tradecli import Trade

logging.basicConfig(level=logging.INFO)

class TF:    
    m1="m1"
    m5="m5"
    m15="m15"
    m30="m30"
    h1="h1"
    h4="h4"
    d="d"
    w="w"
    M="M"
    ALL_TAGS = [m1, m5, m15, m30, h1, h4, d, w, M]
    IGNORED_TAGS = [t for t in ALL_TAGS] 

class PA:
    DEFAULT = False
    
    def type_1_(tf: str):
        return f'type_1_{tf}'
    def type_2_(tf:str):
        return f'type_2_{tf}'
    def type_3_(tf:str):
        return f'type_3_{tf}'
    
    IGNORED_TAGS = []
    
    @staticmethod
    def ALL_TAGS():
        return [PA.type_1_(tf) for tf in TF.ALL_TAGS] + [PA.type_2_(tf) for tf in TF.ALL_TAGS] + [PA.type_3_(tf) for tf in TF.ALL_TAGS]
    
    def used_tags_in(trade: Trade, explicit_search=False) -> list[str]:
        if explicit_search:
            return [t.key for t in trade.tags if t.key in PA.ALL_TAGS]
        if not explicit_search:
            return [t.key for t in trade.tags if t.key.startswith("type_1_") or t.key.startswith("type_2_") or t.key.startswith("type_3_")]
    
    def used_tags_in_df(df: pd.DataFrame, explicit_search=False) -> list[str]:
        if explicit_search:
            return [col for col in df.columns if col in PA.ALL_TAGS]
        if not explicit_search:
            return [col for col in df.columns if col.startswith("type_1_") or col.startswith("type_2_") or col.startswith("type_3_")]
    
    def used_tags_in_df_not_null(df: pd.DataFrame, explicit_search=False) -> list[str]:
        return [col for col in PA.used_tags_in_df(df, explicit_search) if df[col].any()]
    
    def has_PA_tags(trade: Trade) -> bool:
        return any(t for t in trade.tags if t.key in PA.ALL_TAGS)

    def add_tags(trade:Trade, pas:list[str], add_default:bool = False):
        if add_default:
            for pa in PA.ALL_TAGS():
                if pa in pas:
                    trade.add_tag(pa, True)
                else:
                    trade.add_tag(pa, False)
        if not add_default:
            for pa in pas:
                trade.add_tag(pa, True)

    def add_tags_to_df(df: pd.DataFrame):
        df['has_type_1'] = df[[col for col in df.columns if col.startswith('type_1_')]].any(axis=1)
        df['has_type_2'] = df[[col for col in df.columns if col.startswith('type_2_')]].any(axis=1)
        df['has_type_3'] = df[[col for col in df.columns if col.startswith('type_3_')]].any(axis=1)
        df['has_time_frame'] = df[[col for col in df.columns if col in TF.ALL_TAGS]].any(axis=1)
        logging.info(f"Added PA tags to DataFrame. Columns: {df.columns}")

class Confidence:
    TAG_CONFIDENCE = "confidence"
    TAG_NUMERICAL_CONFIDENCE = "numerical_confidence"
    DEFAULT_CONFIDENCE = None
    LEVELS = [1, 2, 3, 4, 5]
    
    @staticmethod
    def add_tags_to_trade(trade: Trade, confidence: int):
        assert confidence in Confidence.LEVELS
        trade.add_tag(Confidence.TAG_NUMERICAL_CONFIDENCE, confidence)
    
    IGNORED_TAGS = [TAG_NUMERICAL_CONFIDENCE] + [f"confidence_{level}" for level in LEVELS]
    CATEGORICAL_TAGS = []

class MultiTimeframeAnalysis:
    TAG_HTF_POI_LTF_CONFIRMATION = "htf_poi_ltf_confirmation"
    DEFAULT_HTF_POI_LTF_CONFIRMATION = None
    TYPE_HTF_POI_LTF_CONFIRMATION = bool
    
    def add_tags_to_trade(trade: Trade, htf_poi_ltf_confirmation: bool):
        assert htf_poi_ltf_confirmation is not None
        trade.add_tag("htf_poi_ltf_confirmation", htf_poi_ltf_confirmation)
    
    IGNORED_TAGS = []
    CATEGORICAL_TAGS = ["htf_poi_ltf_confirmation"]

class POI:
    TAG_POI = "pois"
    DEFAULT_POI = None
    TYPE_POI = list[str]
    
    POI_1H_SC = 'poi_1h_sc'
    POI_1H_LIQUIDITY_GRAB = 'poi_1h_liquidity_grab'
    POI_1H_MITIGATION = 'poi_1h_mitigation'
    
    POI_15M_SC = 'poi_15m_sc'
    POI_15M_LIQUIDITY_GRAB = 'poi_15m_liquidity_grab'
    POI_15M_MITIGATION = 'poi_15m_mitigation'
    
    POI_1M_SC = 'poi_1m_sc'
    POI_1M_LIQUIDITY_GRAB = 'poi_1m_liquidity_grab'
    POI_1M_MITIGATION = 'poi_1m_mitigation'
    
    ALL_TAGS = None
    
    @staticmethod
    def get_poi_tags():
        return [getattr(POI,attr) for attr in dir(POI) if not callable(getattr(POI, attr)) and not attr.startswith("__") and attr.startswith("POI")]
    
    def add_tags(trade: Trade, pois : list[str]):
        trade.add_tag("poi", tuple(list(set(pois))))
        
        for poi in POI.ALL_TAGS:
            if poi in pois:
                trade.add_tag(poi, True)
            if poi not in pois:
                trade.add_tag(poi, False)

POI.ALL_TAGS=POI.get_poi_tags()

class RiskManagement:
    NO_MANAGEMENT = "no_management"
    BE_AFTER_1R = "be_after_1r"
    BE_AFTER_PUSH = "be_after_push"
    CLOSE_EARLY = "close_early"
    
    def add_tags_to_trade(trade: Trade, management_strategy: str):
        if not trade.has_tag("management_strategy"):
            trade.add_tag("management_strategy", management_strategy)
    
    IGNORED_TAGS = []
    CATEGORICAL_TAGS = ["management_strategy"]

class Outcome:
    WIN = "win"
    LOSS = "loss"
    BE_THESHOLD = 0.2
    BE = "be"
    
    @staticmethod
    def get_outcome(rr: float) -> str:
        return Outcome.WIN if rr > 0 else (Outcome.BE if abs(rr) < Outcome.BE_THESHOLD else Outcome.LOSS)
    
    def add_tags_to_trade(trade: Trade):
        rr = next((t.value for t in trade.tags if t.key == "rr"), None)
        if not rr:
            logging.warning(f"Trade {trade.uid} does not have the 'rr' tag")
        
        if rr is not None:
            trade.add_tag("outcome", Outcome.get_outcome(rr))
    
    def add_tags_to_df(df: pd.DataFrame):
        if not "rr" in df.columns:
            raise ValueError("DataFrame must have the 'rr' column")
        
        df["outcome"] = df["rr"].apply(lambda x: Outcome.get_outcome(x))
    
    IGNORED_TAGS = []
    CATEGORICAL_TAGS = ["outcome"]

class TradePosition:
    TAG_ENTRY_PRICE = "entry_price"
    TAG_SL_PRICE = "sl_price"
    TAG_TP_PRICE = "tp_price"
    TAG_SL_DISTANCE = "SL_distance"
    TAG_TP_DISTANCE = "TP_distance"
    TAG_SIDE = "side"
    TAG_RETURN = "return"
    
    DEFAULT_PRICES = None
    
    def __init__(self, entry_price: float, sl_price: float, tp_price: float, close_price: float = None):
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.close_price = close_price

    def add_tags_to_trade(self, trade: Trade):
        trade.add_tag("entry_price", self.entry_price)
        trade.add_tag("sl_price", self.sl_price)
        trade.add_tag("tp_price", self.tp_price)
        if self.close_price is not None:
            trade.add_tag("close_price", self.close_price)
        if self.entry_price is not None and self.sl_price is not None:
            trade.add_tag("SL_distance", self.entry_price - self.sl_price)
        if self.entry_price is not None and self.tp_price is not None:
            trade.add_tag("TP_distance", self.tp_price - self.entry_price)
        if self.entry_price is not None and self.close_price is not None:
            trade.add_tag("return", self.close_price - self.entry_price)
        if self.entry_price is not None and self.sl_price is not None:
            trade.add_tag("side", "long" if self.entry_price > self.sl_price else "short")
    
    IGNORED_TAGS = [TAG_ENTRY_PRICE,TAG_SL_PRICE,TAG_TP_PRICE,TAG_SL_DISTANCE,
                    TAG_TP_DISTANCE,TAG_RETURN]

@dataclass
class PositionEntry:
    """Represents a single entry/position similar to MetaTrader positions"""
    entry_price: float
    lot_size: float
    entry_time: datetime
    sl_price: float
    tp_price: Optional[float] = None
    close_price: Optional[float] = None
    close_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entry setup"""
        if self.sl_price == self.entry_price:
            raise ValueError("SL price cannot be equal to entry price")
    
    @property
    def side(self) -> str:
        """Determine position side based on SL placement"""
        return "long" if self.entry_price > self.sl_price else "short"
    
    def is_closed(self) -> bool:
        """Check if position is closed"""
        return self.close_price is not None
    
    def calculate_pnl(self, price: Optional[float] = None) -> Optional[float]:
        """Calculate PnL at given price or close price"""
        if not price and not self.close_price:
            return None
        
        calc_price = price if price is not None else self.close_price
        multiplier = 1 if self.side == "long" else -1
        return (calc_price - self.entry_price) * self.lot_size * multiplier
    
    def calculate_risk(self) -> float:
        """Calculate risk in price points"""
        return abs(self.entry_price - self.sl_price)
    
    def calculate_reward(self) -> Optional[float]:
        """Calculate potential reward in price points"""
        if not self.tp_price:
            return None
        return abs(self.tp_price - self.entry_price)
    
    def calculate_rr(self) -> Optional[float]:
        """Calculate risk/reward ratio"""
        reward = self.calculate_reward()
        if not reward:
            return None
        return reward / self.calculate_risk()

@dataclass
class ManagedPosition:
    """A container for multiple related entries that form a combined position"""
    TAG_ENTRIES = "position_entries"
    TAG_AVG_ENTRY = "avg_entry_price"
    TAG_TOTAL_LOTS = "total_lot_size"
    TAG_REALIZED_PNL = "realized_pnl"
    TAG_UNREALIZED_PNL = "unrealized_pnl"
    TAG_SIDE = "side"
    
    entries: List[PositionEntry] = field(default_factory=list)
    
    def add_entry(self, price: float, lot_size: float, entry_time: datetime, 
                 sl_price: float, tp_price: Optional[float] = None) -> None:
        """Add a new entry to the position"""
        entry = PositionEntry(
            entry_price=price,
            lot_size=lot_size,
            entry_time=entry_time,
            sl_price=sl_price,
            tp_price=tp_price
        )
        self.entries.append(entry)
    
    def close_partial(self, lot_size: float, close_price: float, close_time: datetime) -> None:
        """Close a portion of the position"""
        remaining_lots = lot_size
        for entry in self.entries:
            if not entry.is_closed() and remaining_lots > 0:
                if entry.lot_size <= remaining_lots:
                    # Close entire entry
                    entry.close_price = close_price
                    entry.close_time = close_time
                    remaining_lots -= entry.lot_size
                else:
                    # Split entry and close part of it
                    new_entry = PositionEntry(
                        entry_price=entry.entry_price,
                        lot_size=entry.lot_size - remaining_lots,
                        entry_time=entry.entry_time,
                        sl_price=entry.sl_price,
                        tp_price=entry.tp_price
                    )
                    entry.lot_size = remaining_lots
                    entry.close_price = close_price
                    entry.close_time = close_time
                    self.entries.append(new_entry)
                    remaining_lots = 0
    
    def close_all(self, close_price: float, close_time: datetime) -> None:
        """Close all open entries in the position"""
        for entry in self.entries:
            if not entry.is_closed():
                entry.close_price = close_price
                entry.close_time = close_time
    
    def get_average_entry(self) -> Optional[float]:
        """Calculate the average entry price weighted by lot size"""
        open_entries = [e for e in self.entries if not e.is_closed()]
        if not open_entries:
            return None
        total_lots = sum(e.lot_size for e in open_entries)
        weighted_sum = sum(e.entry_price * e.lot_size for e in open_entries)
        return weighted_sum / total_lots if total_lots > 0 else None
    
    def get_total_lots(self) -> float:
        """Get total lot size of open positions"""
        return sum(e.lot_size for e in self.entries if not e.is_closed())
    
    def get_realized_pnl(self) -> float:
        """Calculate realized PNL from closed entries"""
        return sum(e.calculate_pnl() or 0 for e in self.entries if e.is_closed())
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PNL based on current market price"""
        return sum(e.calculate_pnl(current_price) or 0 
                  for e in self.entries if not e.is_closed())
    
    def get_dominant_side(self) -> Optional[str]:
        """Get the dominant side based on lot size"""
        long_lots = sum(e.lot_size for e in self.entries 
                       if not e.is_closed() and e.side == "long")
        short_lots = sum(e.lot_size for e in self.entries 
                        if not e.is_closed() and e.side == "short")
        if long_lots == short_lots:
            return None
        return "long" if long_lots > short_lots else "short"
    
    def add_tags_to_trade(self, trade: Trade, current_price: Optional[float] = None) -> None:
        """Add position information as tags to the trade"""
        if not self.entries:
            return
            
        avg_entry = self.get_average_entry()
        if avg_entry:
            trade.add_tag(self.TAG_AVG_ENTRY, avg_entry)
            trade.add_tag(self.TAG_TOTAL_LOTS, self.get_total_lots())
            trade.add_tag(self.TAG_REALIZED_PNL, self.get_realized_pnl())
            
            if current_price:
                trade.add_tag(self.TAG_UNREALIZED_PNL, self.get_unrealized_pnl(current_price))
            
            dominant_side = self.get_dominant_side()
            if dominant_side:
                trade.add_tag(self.TAG_SIDE, dominant_side)
            
            # Add detailed entries information as a structured tag
            entries_data = [
                {
                    "entry_price": e.entry_price,
                    "lot_size": e.lot_size,
                    "entry_time": e.entry_time.isoformat(),
                    "sl_price": e.sl_price,
                    "tp_price": e.tp_price,
                    "side": e.side,
                    "close_price": e.close_price,
                    "close_time": e.close_time.isoformat() if e.close_time else None,
                    "risk": e.calculate_risk(),
                    "reward": e.calculate_reward(),
                    "rr": e.calculate_rr(),
                    "pnl": e.calculate_pnl()
                }
                for e in self.entries
            ]
            trade.add_tag(self.TAG_ENTRIES, entries_data)
    
    IGNORED_TAGS = [TAG_ENTRIES, TAG_AVG_ENTRY, TAG_TOTAL_LOTS, 
                   TAG_REALIZED_PNL, TAG_UNREALIZED_PNL, TAG_SIDE]

class InitialReward:
    TAG_RR = 'initial_risk_reward'
    TAG_RETURN = 'initial_return'
    
    @staticmethod
    def calculate_initial_risk_reward(entry_price: float, sl_price: float, tp_price: float) -> float:
        return (tp_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def calculate_initial_return(entry_price: float, tp_price: float) -> float:
        return tp_price - entry_price
    
    @staticmethod
    def add_tags_to_trade(trade: Trade):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        tp_price = next((t.value for t in trade.tags if t.key == "tp_price"), None)
        if entry_price is not None and sl_price is not None and tp_price is not None:
            rr = InitialReward.calculate_initial_risk_reward(entry_price, sl_price, tp_price)
            trade.add_tag("initial_risk_reward", rr)
            trade.add_tag("initial_return", InitialReward.calculate_initial_return(entry_price, tp_price))
    
    IGNORED_TAGS = [TAG_RR, TAG_RETURN]

class PotentialReward:
    TAG_RR = 'potential_risk_reward'
    TAG_RETURN = 'potential_return'
    TAG_PRICE = 'potential_price'
    
    @staticmethod
    def calculate_potential_risk_reward(entry_price: float, sl_price: float, potential_price: float) -> float:
        return (potential_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def calculate_potential_return(entry_price: float, potential_price: float) -> float:
        return potential_price - entry_price

    @staticmethod
    def add_tags_to_trade(trade: Trade, potential_price: float):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        if entry_price is not None and sl_price is not None:
            rr = PotentialReward.calculate_potential_risk_reward(entry_price, sl_price, potential_price)
            trade.add_tag("potential_risk_reward", rr)
            trade.add_tag("potential_return", PotentialReward.calculate_potential_return(entry_price, potential_price))
            trade.add_tag("potential_price", potential_price)
    
    IGNORED_TAGS = [TAG_RR, TAG_RETURN, TAG_PRICE]

class EntryTime:
    TAG_ENTRY_TIME = "entry_time"
    DEFAULT_ENTRY_TIME = None
    
    def __init__(self, entry_time: datetime):
        self.entry_time = entry_time
            
    def add_tags_to_trade(self, trade: Trade):
        if EntryTime.TAG_ENTRY_TIME not in trade.get_tags_dict():
            trade.add_tag("entry_time", self.entry_time)
        else:
            for tag in trade.tags:
                if tag.key == EntryTime.TAG_ENTRY_TIME:
                    tag.value = self.entry_time
                    break
    
    IGNORED_TAGS = ["entry_time"]

class Sessions:
    TAG_SESSION = "session"
    DEFAULT_SESSION = None
    LONDON = "london"
    NEW_YORK = "new_york"
    TOKYO = "tokyo"
    
    def session_from_ts(ts: pd.Timestamp) -> str:
        session = None
        if ts.hour >= 7 and ts.hour < 13:
            session = Sessions.LONDON
        elif ts.hour >= 13 and ts.hour < 20:
            session = Sessions.NEW_YORK
        elif ts.hour >= 20 or ts.hour < 7:
            session = Sessions.TOKYO
        return session
    
    def add_tags_to_trade(ts: pd.Timestamp, trade: Trade):
        if ts is not None:
            session = Sessions.session_from_ts(ts)
            trade.add_tag("session", session)
    
    def add_tags_to_trade(trade: Trade):
        ts = next((t.value for t in trade.tags if t.key == EntryTime.TAG_ENTRY_TIME), None)
        if ts is not None:
            session = Sessions.session_from_ts(ts)
            trade.add_tag("session", session)
    
    IGNORED_TAGS = []

class RR:
    TAG_RR = "rr"
    DEFAULT_RR = 0.0
    
    @staticmethod
    def calculate_risk_reward_ratio(entry_price: float, sl_price: float, close_price: float) -> float:
        return (close_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def add_tags_to_trade(trade: Trade):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        close_price = next((t.value for t in trade.tags if t.key == "close_price"), None)
        prices = [entry_price, sl_price, close_price]
        
        if entry_price is not None and sl_price is not None and close_price is not None:
            rr = RR.calculate_risk_reward_ratio(entry_price, sl_price, close_price)
            trade.add_tag(RR.TAG_RR, rr)
        else:
            logging.warning(f'trade {trade.uid}: RR calculation failed. Some prices are missing: { dict(zip(["entry_price", "sl_price", "close_price"], prices)) }')
    
    IGNORED_TAGS = []

@dataclass
class Account:
    account_name: str

    IGNORED_TAGS = ["account_name"]
    CATEGORICAL_TAGS = ["account_name"]
    
    DEFAULT = "default"

    @staticmethod
    def add_default(trade: Trade):
        trade.add_tag("account_name", Account.DEFAULT)
    
    @staticmethod
    def add_account_to_trade(trade: Trade, account_name: str):
        trade.add_tag("account", account_name)

# Constants
ACC_IDEAL = "ideal"
ACC_MT5_VANTAGE = "mt5_vantage"
ACC_TEST = "test_account"
TYPE_3_M15 = PA.type_3_(TF.m15)

def get_all_ignored_tags() -> List[str]:
    ignored_tags = []
    classes = [TF, PA, Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome, TradePosition, InitialReward, PotentialReward, EntryTime, Sessions, RR]
    for cls in classes:
        ignored_tags.extend(cls.IGNORED_TAGS)
    return ignored_tags

def get_all_categorical_tags() -> List[str]:
    categorical_tags = []
    classes = [Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome]
    for cls in classes:
        categorical_tags.extend(cls.CATEGORICAL_TAGS)
    return categorical_tags

@dataclass
class PositionModification:
    """Represents a modification to a position (size change, price levels change, etc.)"""
    timestamp: datetime
    price: float  # Price at modification time
    old_lot_size: float
    new_lot_size: float
    old_sl: Optional[float] = None
    new_sl: Optional[float] = None
    old_tp: Optional[float] = None
    new_tp: Optional[float] = None
    pnl: Optional[float] = None  # PnL realized if this was a size reduction

@dataclass
class ModifiablePosition:
    """A single position that can be modified over time (like in cTrader)"""
    TAG_INITIAL_ENTRY = "initial_entry"
    TAG_CURRENT_SIZE = "current_size"
    TAG_CURRENT_AVG_PRICE = "current_avg_price"
    TAG_CURRENT_SL = "current_sl"
    TAG_CURRENT_TP = "current_tp"
    TAG_SIDE = "side"
    TAG_MODIFICATIONS = "modifications"
    TAG_REALIZED_PNL = "realized_pnl"
    TAG_UNREALIZED_PNL = "unrealized_pnl"
    
    # Initial position state
    entry_time: datetime
    side: str  # "long" or "short"
    initial_price: float
    initial_lot_size: float
    initial_sl: float
    initial_tp: Optional[float] = None
    
    # Current position state
    current_lot_size: float = field(init=False)
    current_avg_price: float = field(init=False)
    current_sl: float = field(init=False)
    current_tp: Optional[float] = field(init=False)
    
    # History of modifications
    modifications: List[PositionModification] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize current state with initial values"""
        if self.side not in ["long", "short"]:
            raise ValueError("Side must be 'long' or 'short'")
        self.current_lot_size = self.initial_lot_size
        self.current_avg_price = self.initial_price
        self.current_sl = self.initial_sl
        self.current_tp = self.initial_tp
    
    def modify_size(self, timestamp: datetime, price: float, new_lot_size: float) -> None:
        """Modify position size (scale in/out) at given price"""
        if new_lot_size < 0:
            raise ValueError("New lot size cannot be negative")
            
        if new_lot_size > self.current_lot_size:
            # Scaling in - adjust average price
            additional_size = new_lot_size - self.current_lot_size
            self.current_avg_price = (
                (self.current_avg_price * self.current_lot_size + price * additional_size)
                / new_lot_size
            )
        elif new_lot_size < self.current_lot_size:
            # Scaling out - calculate realized PnL
            reduced_size = self.current_lot_size - new_lot_size
            pnl = self._calculate_pnl(price, reduced_size)
        else:
            # No change
            return
            
        mod = PositionModification(
            timestamp=timestamp,
            price=price,
            old_lot_size=self.current_lot_size,
            new_lot_size=new_lot_size,
            old_sl=self.current_sl,
            new_sl=self.current_sl,
            old_tp=self.current_tp,
            new_tp=self.current_tp,
            pnl=pnl if new_lot_size < self.current_lot_size else None
        )
        self.modifications.append(mod)
        self.current_lot_size = new_lot_size
    
    def modify_sl(self, timestamp: datetime, new_sl: float) -> None:
        """Modify stop loss level"""
        # Validate SL placement based on side
        if self.side == "long" and new_sl >= self.current_avg_price:
            raise ValueError("Stop loss must be below entry for long positions")
        if self.side == "short" and new_sl <= self.current_avg_price:
            raise ValueError("Stop loss must be above entry for short positions")
            
        mod = PositionModification(
            timestamp=timestamp,
            price=self.current_avg_price,  # Use avg price as no actual execution
            old_lot_size=self.current_lot_size,
            new_lot_size=self.current_lot_size,
            old_sl=self.current_sl,
            new_sl=new_sl,
            old_tp=self.current_tp,
            new_tp=self.current_tp
        )
        self.modifications.append(mod)
        self.current_sl = new_sl
    
    def modify_tp(self, timestamp: datetime, new_tp: Optional[float]) -> None:
        """Modify take profit level"""
        if new_tp is not None:
            # Validate TP placement based on side
            if self.side == "long" and new_tp <= self.current_avg_price:
                raise ValueError("Take profit must be above entry for long positions")
            if self.side == "short" and new_tp >= self.current_avg_price:
                raise ValueError("Take profit must be below entry for short positions")
                
        mod = PositionModification(
            timestamp=timestamp,
            price=self.current_avg_price,  # Use avg price as no actual execution
            old_lot_size=self.current_lot_size,
            new_lot_size=self.current_lot_size,
            old_sl=self.current_sl,
            new_sl=self.current_sl,
            old_tp=self.current_tp,
            new_tp=new_tp
        )
        self.modifications.append(mod)
        self.current_tp = new_tp
    
    def _calculate_pnl(self, price: float, lot_size: float) -> float:
        """Calculate PnL for a given price and lot size"""
        multiplier = 1 if self.side == "long" else -1
        return (price - self.current_avg_price) * lot_size * multiplier
    
    def get_realized_pnl(self) -> float:
        """Get total realized PnL from all modifications"""
        return sum(mod.pnl or 0 for mod in self.modifications)
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL at current price"""
        return self._calculate_pnl(current_price, self.current_lot_size)
    
    def get_risk_reward(self) -> Optional[float]:
        """Calculate current risk/reward ratio"""
        if not self.current_tp:
            return None
        risk = abs(self.current_avg_price - self.current_sl)
        reward = abs(self.current_tp - self.current_avg_price)
        return reward / risk if risk != 0 else None
    
    def add_tags_to_trade(self, trade: Trade, current_price: Optional[float] = None) -> None:
        """Add position information as tags to the trade"""
        # Initial state
        trade.add_tag(self.TAG_INITIAL_ENTRY, {
            "time": self.entry_time.isoformat(),
            "side": self.side,
            "price": self.initial_price,
            "lot_size": self.initial_lot_size,
            "sl": self.initial_sl,
            "tp": self.initial_tp
        })
        
        # Current state
        trade.add_tag(self.TAG_CURRENT_SIZE, self.current_lot_size)
        trade.add_tag(self.TAG_CURRENT_AVG_PRICE, self.current_avg_price)
        trade.add_tag(self.TAG_CURRENT_SL, self.current_sl)
        if self.current_tp:
            trade.add_tag(self.TAG_CURRENT_TP, self.current_tp)
        trade.add_tag(self.TAG_SIDE, self.side)
        
        # Modifications history
        mods_data = [
            {
                "time": mod.timestamp.isoformat(),
                "price": mod.price,
                "old_size": mod.old_lot_size,
                "new_size": mod.new_lot_size,
                "old_sl": mod.old_sl,
                "new_sl": mod.new_sl,
                "old_tp": mod.old_tp,
                "new_tp": mod.new_tp,
                "realized_pnl": mod.pnl
            }
            for mod in self.modifications
        ]
        trade.add_tag(self.TAG_MODIFICATIONS, mods_data)
        
        # PnL information
        trade.add_tag(self.TAG_REALIZED_PNL, self.get_realized_pnl())
        if current_price:
            trade.add_tag(self.TAG_UNREALIZED_PNL, self.get_unrealized_pnl(current_price))
    
    IGNORED_TAGS = [TAG_INITIAL_ENTRY, TAG_CURRENT_SIZE, TAG_CURRENT_AVG_PRICE,
                   TAG_CURRENT_SL, TAG_CURRENT_TP, TAG_SIDE, TAG_MODIFICATIONS,
                   TAG_REALIZED_PNL, TAG_UNREALIZED_PNL] 