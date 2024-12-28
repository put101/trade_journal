from datetime import datetime
from tradecli import *
import markdown
import os

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

class PA:
    DEFAULT = False
    
    def type_1_(tf: str):
        return f'type_1_{tf}'
    def type_2_(tf:str):
        return f'type_2_{tf}'
    def type_3_(tf:str):
        return f'type_3_{tf}'

class Confidence:
    TAG_CONFIDENCE = "confidence"
    DEFAULT_CONFIDENCE = None
    
    def add_tags_to_trade(trade: Trade, confidence: int):
        assert confidence is not None
        trade.add_tag("confidence", confidence)
    
class MultiTimeframeAnalysis:
    TAG_HTF_POI_LTF_CONFIRMATION = "htf_poi_ltf_confirmation"
    DEFAULT_HTF_POI_LTF_CONFIRMATION = None
    TYPE_HTF_POI_LTF_CONFIRMATION = bool
    
    def add_tags_to_trade(trade: Trade, htf_poi_ltf_confirmation: bool):
        assert htf_poi_ltf_confirmation is not None
        trade.add_tag("htf_poi_ltf_confirmation", htf_poi_ltf_confirmation)

class RiskManagement:
    """Self explanatory.
    """
    NO_MANAGEMENT = "no_management"
    BE_AFTER_1R = "be_after_1r"
    BE_AFTER_PUSH = "be_after_push"
    CLOSE_EARLY = "close_early"
    
    def add_tags_to_trade(trade: Trade, management_strategy: str):
        if not trade.has_tag("management_strategy"):
            trade.add_tag("management_strategy", management_strategy)

class Outcome:
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    def add_tags_to_trade(trade: Trade, outcome: str):
        trade.add_tag("outcome", outcome)
    
    def add_tags_to_trade_auto(trade: Trade):
        if trade.has_tag("outcome"):
            return None # already has outcome
        
        ret = next((t.value for t in trade.tags if t.key == "return"), None)
        if ret is None:
            return None
        
        if ret > 0:
            outcome = Outcome.WIN
        elif ret < 0:
            outcome = Outcome.LOSS
        else:
            outcome = Outcome.BREAKEVEN
        
        trade.add_tag("outcome", outcome)
       
    def add_tags_to_df(df: pd.DataFrame):
        df['outcome'] = df['return'].apply(lambda x: Outcome.WIN if x > 0 else (Outcome.LOSS if x < 0 else Outcome.BREAKEVEN))
    
TYPE_3_M15 = PA.type_3_(TF.m15)
        
ALL_TAGS = frozenset(TF.ALL_TAGS + [PA.type_1_(tf) for tf in TF.ALL_TAGS] + [PA.type_2_(tf) for tf in TF.ALL_TAGS])
print(ALL_TAGS)

class TradePosition:
    TAG_ENTRY_PRICE = "entry_price"
    TAG_SL_PRICE = "sl_price"
    TAG_TP_PRICE = "tp_price"
    TAG_SL_DISTANCE = "SL_distance"
    TAG_TP_DISTANCE = "TP_distance"
    TAG_SIDE = "side" # long, short
    TAG_RETURN = "return"
    
    DEFAULT_PRICES = None
    
    def __init__(self, trade_uid: str, entry_price: float, sl_price: float, tp_price: float, close_price: float = None):
        self.trade_uid = trade_uid
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

class InitialReward:
    """Represents the initial planned reward and risk reward ratio of a trade.
    """
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
        

class RR:
    TAG_RR = "risk_reward_ratio"
    DEFAULT_RR = 0.0
    
    @staticmethod
    def calculate_risk_reward_ratio(entry_price: float, sl_price: float, tp_price: float) -> float:
        return (tp_price - entry_price) / (entry_price - sl_price)
    @staticmethod
    def add_tags_to_trade(trade: Trade):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        tp_price = next((t.value for t in trade.tags if t.key == "tp_price"), None)
        if entry_price is not None and sl_price is not None and tp_price is not None:
            rr = RR.calculate_risk_reward_ratio(entry_price, sl_price, tp_price)
            trade.add_tag("risk_reward_ratio", rr)

journal = TradeJournal()

t = Trade(uid="1")
t.add_tag(PA.type_1_(TF.m1), True)
t.add_tag(TYPE_3_M15, True)
journal.add_trade(t)
position = TradePosition(trade_uid="1", entry_price=1.1000, sl_price=1.0950, tp_price=1.1100)
position.add_tags_to_trade(t)
EntryTime(entry_time=datetime.now()).add_tags_to_trade(t)
RR.add_tags_to_trade(t)

t = Trade(uid="2")
t.add_tag(PA.type_2_(TF.h1), True)
journal.add_trade(t)
position = TradePosition(trade_uid="2", entry_price=1.2000, sl_price=1.1850, tp_price=1.2100, close_price=1.1855)
position.add_tags_to_trade(t)
EntryTime(entry_time=datetime.now()).add_tags_to_trade(t)
RR.add_tags_to_trade(t)
MultiTimeframeAnalysis.add_tags_to_trade(t, True)


t = Trade(uid="3")
t.add_tag("SL_distance", 0.5)
journal.add_trade(t)
position = TradePosition(trade_uid="3", entry_price=1.3000, sl_price=1.2970, tp_price=1.3300)
position.add_tags_to_trade(t)
EntryTime(entry_time=pd.Timestamp("2024-12-27 10:00:01")).add_tags_to_trade(t)
MultiTimeframeAnalysis.add_tags_to_trade(t, False)


t = t.copy()
t.uid = "4"
t.add_tag("management_strategy", "strategy_2")
position = TradePosition(trade_uid="4", entry_price=1.3000, sl_price=1.2950, tp_price=1.9100, close_price=1.3050)
position.add_tags_to_trade(t)
EntryTime(entry_time=pd.Timestamp("2024-12-25 10:00:00")).add_tags_to_trade(t)
RR.add_tags_to_trade(t)
journal.add_trade(t)
PotentialReward.add_tags_to_trade(t, 1.3150)
Confidence.add_tags_to_trade(t, 4)
MultiTimeframeAnalysis.add_tags_to_trade(t, True)

# add defaults to all trades or certain tags that should not be None
for trade in journal.trades:
    Sessions.add_tags_to_trade(trade)
    RR.add_tags_to_trade(trade)
    Outcome.add_tags_to_trade_auto(trade)
    InitialReward.add_tags_to_trade(trade)
    RiskManagement.add_tags_to_trade(trade, RiskManagement.NO_MANAGEMENT)
    
print(journal.trades)

full_df = journal.to_dataframe()