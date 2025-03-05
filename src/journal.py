from datetime import datetime
import markdown
import os
import random
import logging
import re  # Add regex module for pattern matching
import scipy
from src.tradecli import * 

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
    
    def has_PA_tags(trade: Trade) -> bool:
        return any(t for t in trade.tags if t.key in PA.ALL_TAGS)

    def add_tags(trade:Trade, pas:list[str]):
        for pa in PA.ALL_TAGS():
            if pa in pas:
                trade.add_tag(pa, True)
            else:
                trade.add_tag(pa, False)

    def add_tags_to_df(df: pd.DataFrame):
        # Add additional features/tags
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
        trade.add_tag(Confidence.TAG_NUMERICAL_CONFIDENCE, confidence)  # Add numerical confidence
    
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

## START POI
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
    
    # set the ALL_TAGS after the class is ready (POI class is defined)
    ALL_TAGS = None
    
    # all Tgas are the specific POIs, get them from class definiton starting with POI_    
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
## END POI        

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
    
    IGNORED_TAGS = []
    CATEGORICAL_TAGS = ["management_strategy"]

class Outcome:
    """Categorical variable, win or loss (breakeven if below a certain threshold).
    Uses 'rr' tag to determine the outcome.
    """
    
    WIN = "win"
    LOSS = "loss"
    BE_THESHOLD = 0.2 # Breakeven threshold (pos and neg)
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


TYPE_3_M15 = PA.type_3_(TF.m15)


class TradePosition:
    TAG_ENTRY_PRICE = "entry_price"
    TAG_SL_PRICE = "sl_price"
    TAG_TP_PRICE = "tp_price"
    TAG_SL_DISTANCE = "SL_distance"
    TAG_TP_DISTANCE = "TP_distance"
    TAG_SIDE = "side" # long, short
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
    """Risk Reward Ratio (Actual / Closed)
    """
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


ACC_IDEAL = "ideal"
ACC_MT5_VANTAGE = "mt5_vantage"
ACC_TEST = "test_account"

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

j = TradeJournal()
j.get_all_categorical_tags = get_all_categorical_tags
j.get_all_ignored_tags = get_all_ignored_tags


### TEST DATA START

# Define distributions for different tags
confidence_levels = [1, 2, 3, 4, 5]
management_strategies = [RiskManagement.NO_MANAGEMENT, RiskManagement.BE_AFTER_1R, RiskManagement.BE_AFTER_PUSH, RiskManagement.CLOSE_EARLY]
timeframes = TF.ALL_TAGS

logging.info("Adding more trades to the journal")
# Add more entries to the journal using a loop with random choices
for i in range(5, 15):
    t = Trade(uid=str(1000+i))
    t.add_tag(random.choice([PA.type_1_(tf) for tf in timeframes]), True)
    t.add_tag(random.choice([PA.type_2_(tf) for tf in timeframes]), True)
    t.add_tag(random.choice([PA.type_3_(tf) for tf in timeframes]), True)
    t.add_tag("unit_test", True)  # Add unit_test tag
    Account.add_account_to_trade(t, "test_account")  # Add account tag
    j.add_trade(t)
    entry_price = round(1.1000 + random.uniform(0.01, 0.05), 4)
    # long and short trades, with possible SL and TP    
    is_long = random.choice([True, False])
    rr = random.uniform(1, 10.0)
    WR = 0.7
    SL_POINTS = 0.005
    SL_POINTS_VARIANCE = 0.001
    is_win = random.choices([True, False], weights=[WR, 1-WR], k=1)[0]
    
    
    if is_win:
        actual_rr = random.uniform(0, 10.0)
    else:
        actual_rr = random.uniform(-1.50, 0)
        
    actual_rr = round(actual_rr, 2)
    
    
    if is_long:
        entry_price = round(entry_price, 4)
        sl_price = entry_price - SL_POINTS
        tp_price = entry_price + SL_POINTS * rr
        close_price = entry_price + SL_POINTS * actual_rr
    else:
        entry_price = round(entry_price, 4)
        sl_price = entry_price + SL_POINTS
        tp_price = entry_price - SL_POINTS * rr
        close_price = entry_price - SL_POINTS * actual_rr
    
    position = TradePosition(entry_price=entry_price, sl_price=sl_price, tp_price=tp_price, close_price=close_price)
    position.add_tags_to_trade(t)
    # choose random entry timestamp date, hour, minue within the last 30 days from now
    # the date should around each working day of the week
    # the hour should be normally distributed around 09:00 GMT+2, tz="Europe/Berlin"
    # the minute should be normally distributed around 00, 15, 30, 45
    hour = scipy.stats.truncnorm.rvs(-1, 1, loc=9, scale=1)
    minute = random.choice([0, 15, 30, 45])
    minute = scipy.stats.truncnorm.rvs(-1, 1, loc=minute, scale=15) # Normally distributed around 0, 15, 30, 45
    entry_time = pd.Timestamp.now() + pd.Timedelta(days=random.randint(-30, 0), hours=hour, minutes=minute)
    # convert the timestamp 
    EntryTime(entry_time=entry_time).add_tags_to_trade(t)
    #EntryTime(entry_time=datetime.now()).add_tags_to_trade(t)
    RR.add_tags_to_trade(t)
    Outcome.add_tags_to_trade(t)
    MultiTimeframeAnalysis.add_tags_to_trade(t, random.choice([True, False]))
    Confidence.add_tags_to_trade(t, random.choice(confidence_levels))  # Ensure confidence is added    
    RiskManagement.add_tags_to_trade(t, random.choice(management_strategies))

## TEST DATA END

def create_ideal_trade(uid: str, entry_price: float, sl_price: float, tp_price: float, close_price: Optional[float] = None) -> Trade:
    trade = Trade(uid=uid, execution_type="ideal")
    position = TradePosition(trade_uid=uid, entry_price=entry_price, sl_price=sl_price, tp_price=tp_price, close_price=close_price)
    position.add_tags_to_trade(trade)
    EntryTime(entry_time=datetime.now()).add_tags_to_trade(trade)
    RR.add_tags_to_trade(trade)
    Outcome.add_tags_to_trade(trade)
    MultiTimeframeAnalysis.add_tags_to_trade(trade, random.choice([True, False]))
    Confidence.add_tags_to_trade(trade, random.choice(confidence_levels))
    RiskManagement.add_tags_to_trade(trade, RiskManagement.NO_MANAGEMENT)
    return trade

# Example of tracking one setup with actual account execution and ideal execution
logging.info("Creating example trades for actual and ideal executions")


t1 = None #TODO
t2 = Trade(uid="2")
t2.add_tag('taken', True)
Account.add_account_to_trade(t2, ACC_MT5_VANTAGE)
EntryTime(pd.Timestamp('2025-02-18 14:10:00')).add_tags_to_trade(t2)
TradePosition(entry_price=2914.03,sl_price=2910.94, tp_price=3000.0, close_price=None).add_tags_to_trade(t2)

print(t2)
j.add_trade(t2)

t4 = Trade(uid="4")
Account.add_account_to_trade(t4, ACC_IDEAL)
EntryTime(pd.Timestamp('2025-02-22 15:11:00')).add_tags_to_trade(t4)
# limit order, tp hit
TradePosition(entry_price=22_164.40, sl_price=22_179.09, tp_price=22_105.27, close_price=22_105.27).add_tags_to_trade(t4)
PotentialReward.add_tags_to_trade(t4, 21_600.00)
RiskManagement.add_tags_to_trade(t4, RiskManagement.BE_AFTER_PUSH)
Confidence.add_tags_to_trade(t4, 5)
POI.add_tags(t4, [POI.POI_1H_SC, POI.POI_1H_LIQUIDITY_GRAB, POI.POI_1M_SC])
MultiTimeframeAnalysis.add_tags_to_trade(t4, True)
PA.add_tags(t4, [PA.type_1_(TF.m15), PA.type_1_(TF.m5), PA.type_3_(TF.m1)])
j.add_trade(t4)


logging.info("Adding default tags to all trades")
# add defaults to all trades or certain tags that should not be None
for trade in j.trades:
    Sessions.add_tags_to_trade(trade)
    RR.add_tags_to_trade(trade)
    InitialReward.add_tags_to_trade(trade)
    # DEFAULTS
    RiskManagement.add_tags_to_trade(trade, RiskManagement.NO_MANAGEMENT)
    # set False for the PA tags that are not set
    for tag in PA.ALL_TAGS():
        if not trade.has_tag(tag):
            trade.add_tag(tag, False)


def get_full_df():
    return j.to_dataframe().copy()

get_number_of_trades = lambda df: len(df)
get_set_of_tags = lambda df: frozenset([tag for tag in df.columns if tag != "uid"])
get_number_of_tags = lambda df: len(get_set_of_tags(df))
get_number_of_trades_with_tag = lambda df, tag: len(df[df[tag].notnull()])


# debug
print(t4)