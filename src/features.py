# src/features.py
""" 
This file is used to define the features that are used in the journal.

Each feature is defined as a class that has a set of tags or features, which is used interchangeably.

The features are used to create a feature dataframe, which is used to train the model and trading analyis.



"""

from datetime import datetime
import logging
import random
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import scipy.stats
from tradecli import Trade
from trade_old import *
from IPython.display import display  # Import display for Jupyter Notebook
import utils

logging.basicConfig(level=logging.INFO)

from typing import Type
from abc import ABC, abstractmethod

class Feature(ABC):
    @abstractmethod
    def add_tags_to_trade(self, trade: Execution):
        pass

class BaseFeature(Feature):
    @staticmethod
    def ALL_TAGS() -> List[str]:
        return []

    @staticmethod
    def IGNORED_TAGS() -> List[str]:
        return []

    @staticmethod
    def CATEGORICAL_TAGS() -> List[str]:
        return []

    @staticmethod
    def FLOAT_TAGS() -> List[str]:
        return []

    @staticmethod
    def DATETIME_TAGS() -> List[str]:
        return []

    def add_tags_to_trade(self, trade: Execution):
        pass
    
    @classmethod
    def sanity_check(cls, df: pd.DataFrame):
        """Provides autmoatic sanity checks on a full trade journal dataframe to spot obvious user or data errors."""
        cls._sanity_ok( "(pass)")

    @classmethod
    def _sanity_ok(cls, txt=''):      
        utils.green_print(f"OK - {cls.__name__} sanity check: " + str(txt))
    
    @classmethod
    def _sanity_fail(cls, txt):
        utils.pink_print(f"FAILED - {cls.__name__} sanity check: " + str(txt))
        

def reorder_dataframe_columns(
    df: pd.DataFrame, 
    fixed_features: List[str], 
    feature_classes: List[Union[str, Type[BaseFeature]]]
) -> pd.DataFrame:
    """
    Reorder DataFrame columns based on a predefined order of fixed features and feature classes.

    Parameters:
    - df: The DataFrame to reorder.
    - fixed_features: A list of column names that should appear first in the specified order.
    - feature_classes: A list of classes or strings whose ALL_TAGS() will be used to determine the order of columns.

    Returns:
    - A new DataFrame with columns reordered.
    """
    # Initialize an empty list to hold the ordered columns
    ordered_columns = []

    # Add fixed features first, ensuring they are unique
    for feature in fixed_features:
        if feature in df.columns and feature not in ordered_columns:
            ordered_columns.append(feature)

    # Add columns from each class in the specified order
    # Add columns from each class in the specified order
    for item in feature_classes:
        if isinstance(item, str):
            # If it's a string, just add it if it exists in the DataFrame
            if item in df.columns and item not in ordered_columns:
                ordered_columns.append(item)
        elif isinstance(item, type) and issubclass(item, BaseFeature):
            # If it's a class, add all its tags
            for tag in item.ALL_TAGS():
                if tag in df.columns and tag not in ordered_columns:
                    ordered_columns.append(tag)
        else:
            raise ValueError(f'item: {item} is not str or a subclass of BaseFeature: {BaseFeature}')

    logging.debug('ordered_columns: ' + str(ordered_columns))
    # Get the remaining columns that are not in the ordered list
    remaining_columns = [col for col in df.columns if col not in ordered_columns]
    logging.debug('remaining_columns: ' + str(remaining_columns))
    # Combine the ordered columns with the remaining columns
    final_order = ordered_columns + remaining_columns
    
    df_sorted = df[final_order]
    
    assert len(df.columns) == len(df_sorted.columns)
    assert set(df.columns) == set(df.columns)
    
    return df_sorted 


## UTILS

def dict_add_tags(trade: Trade, d: dict):
    # add any dict of key_values to a trade
    trade.add_dict(d)


class TF(BaseFeature):
    m1="m1"
    m5="m5"
    m15="m15"
    m30="m30"
    h1="h1"
    h4="h4"
    d="d"
    w="w"
    M="M"
    
    @staticmethod
    def ALL_TAGS():
        return [TF.m1, TF.m5, TF.m15, TF.m30, TF.h1, TF.h4, TF.d, TF.w, TF.M]

    @staticmethod
    def IGNORED_TAGS():
        return [t for t in TF.ALL_TAGS()]

class PA(BaseFeature):
    DEFAULT = False
    
    def type_1_(tf: str):
        return f'type_1_{tf}'
    def type_2_(tf:str):
        return f'type_2_{tf}'
    def type_3_(tf:str):
        return f'type_3_{tf}'
    
    @staticmethod
    def ALL_TAGS():
        return [PA.type_1_(tf) for tf in TF.ALL_TAGS()] + [PA.type_2_(tf) for tf in TF.ALL_TAGS()] + [PA.type_3_(tf) for tf in TF.ALL_TAGS()]
    
    def used_tags_in(trade: Execution, explicit_search=False) -> list[str]:
        if explicit_search:
            return [t.key for t in trade.tags if t.key in PA.ALL_TAGS()]
        if not explicit_search:
            return [t.key for t in trade.tags if t.key.startswith("type_1_") or t.key.startswith("type_2_") or t.key.startswith("type_3_")]
    
    def used_tags_in_df(df: pd.DataFrame, explicit_search=False) -> list[str]:
        if explicit_search:
            return [col for col in df.columns if col in PA.ALL_TAGS()]
        if not explicit_search:
            return [col for col in df.columns if col.startswith("type_1_") or col.startswith("type_2_") or col.startswith("type_3_")]
    
    def used_tags_in_df_not_null(df: pd.DataFrame, explicit_search=False) -> list[str]:
        return [col for col in PA.used_tags_in_df(df, explicit_search) if df[col].any()]
    
    def has_PA_tags(trade: Execution) -> bool:
        return any(t for t in trade.tags if t.key in PA.ALL_TAGS())

    def add_tags(trade:Execution, pas:list[str], add_default:bool = False):
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
        df['has_time_frame'] = df[[col for col in df.columns if col in TF.ALL_TAGS()]].any(axis=1)
        logging.info(f"Added PA tags to DataFrame. Columns: {df.columns}")

class Confidence(BaseFeature):

    TAG_ORDINAL_CONFIDENCE = "numerical_confidence"
    DEFAULT_CONFIDENCE = None
    LEVELS = [1, 2, 3, 4, 5]

    @staticmethod
    def ALL_TAGS():
        return [Confidence.TAG_ORDINAL_CONFIDENCE] + [f"confidence_{level}" for level in Confidence.LEVELS]
    
    @staticmethod
    def add_tags_to_trade(trade: Execution, confidence: int):
        assert confidence in Confidence.LEVELS
        trade.add_tag(Confidence.TAG_ORDINAL_CONFIDENCE, confidence)

class MultiTimeframeAnalysis(BaseFeature):
    TAG_HTF_POI_LTF_CONFIRMATION = "htf_poi_ltf_confirmation"
    DEFAULT_HTF_POI_LTF_CONFIRMATION = None
    TYPE_HTF_POI_LTF_CONFIRMATION = bool
    
    def add_tags_to_trade(trade: Execution, htf_poi_ltf_confirmation: bool):
        assert htf_poi_ltf_confirmation is not None
        trade.add_tag("htf_poi_ltf_confirmation", htf_poi_ltf_confirmation)
    
    @staticmethod
    def ALL_TAGS():
        return [MultiTimeframeAnalysis.TAG_HTF_POI_LTF_CONFIRMATION]
    
    @staticmethod
    def CATEGORICAL_TAGS():
        return [MultiTimeframeAnalysis.TAG_HTF_POI_LTF_CONFIRMATION]

class POI(BaseFeature):
    TAG_POI = "pois"
    DEFAULT_POI = 'NO_POI'
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
    
    @staticmethod
    def ALL_TAGS():
        return [
            POI.POI_1H_SC, POI.POI_1H_LIQUIDITY_GRAB, POI.POI_1H_MITIGATION,
            POI.POI_15M_SC, POI.POI_15M_LIQUIDITY_GRAB, POI.POI_15M_MITIGATION,
            POI.POI_1M_SC, POI.POI_1M_LIQUIDITY_GRAB, POI.POI_1M_MITIGATION
        ]
    
    @staticmethod
    def get_poi_tags():
        return POI.ALL_TAGS()
    
    @staticmethod
    def add_tags(trade: Execution, pois: list[str]):
        trade.add_tag("poi", tuple(list(set(pois))))
        
        for poi in POI.ALL_TAGS():
            trade.add_tag(poi, poi in pois)

    @staticmethod
    def get_cols_df(df: pd.DataFrame) -> List[str]:
        """Return a list of relevant POI columns from the DataFrame."""
        return [col for col in df.columns if any(poi in col for poi in POI.ALL_TAGS())]

    @classmethod
    def get_used_tags_df(cls, df: pd.DataFrame) -> List[str]:
        """Return a list of POI tags used in the DataFrame."""
        used_tags = []
        for col in df.columns:
            for tag in cls.ALL_TAGS():
                if tag in col:
                    used_tags.append(tag)
        return list(set(used_tags))  # Return unique tags

    @classmethod
    def summary(cls, df: pd.DataFrame):
        """Print a summary of POIs used and not used in the DataFrame."""
        used_tags = cls.get_used_tags_df(df)
        all_tags = cls.ALL_TAGS()

        used = set(used_tags)
        not_used = set(all_tags) - used

        print("Summary of POIs:")
        print(f"Used POIs: {', '.join(used) if used else 'None'}")
        print(f"Not Used POIs: {', '.join(not_used) if not_used else 'No, i.e All POIs are used'}")

    @classmethod
    def sanity_check(cls, df: pd.DataFrame, threshold: float = 0.5, use_warn=False, use_display=False):
        """Check the POI columns for valid values and report statistics."""
        poi_columns = cls.get_cols_df(df)

        failed = []        # Create a DataFrame to hold the results
        results = []
        
        #for col in poi_columns:
        for col in ['poi']:
            valid_count = df[col].notna().sum()
            total_count = len(df[col])
            valid_ratio = valid_count / total_count if total_count > 0 else 0
            
            results.append({
                'Column': col,
                'Valid Count': valid_count,
                'Total Count': total_count,
                'Valid Ratio': valid_ratio
            })
            
            if valid_ratio < threshold:
                failed.append(f"Column '{col}' has a low valid ratio ({valid_ratio:.2f}), consider checking the data." )
                if use_warn:
                    logging.warn(f"Warning: Column '{col}' has a low valid ratio ({valid_ratio:.2f}), consider checking the data.")

        # Create a DataFrame from the results
        results_df = pd.DataFrame(results)
                
        def highlight_issues(row):
            # Create a list with no style for all columns by default
            styles = ['' for _ in row.index]
            # Get the index of the 'Valid Ratio' column
            idx = row.index.get_loc('Valid Ratio')
            if row['Valid Ratio'] < threshold:
                styles[idx] = 'background-color: salmon'
            return styles

        results_df_styled = results_df.style.apply(highlight_issues, axis=1)
        if use_display:
            display(results_df_styled)



        if not failed:
            cls._sanity_ok()
        else:
            cls._sanity_fail(str(failed))

class RiskManagement(BaseFeature):
    
    FEATURE_MANAGEMENT_STRATEGY = "management_strategy"
    NO_MANAGEMENT = "no_management"
    BE_AFTER_1R = "be_after_1r"
    BE_AFTER_PUSH = "be_after_push"
    CLOSE_EARLY = "close_early"
    
    DEFAULT_MANAGEMENT_STRATEGY = NO_MANAGEMENT
    
    @staticmethod
    def ALL_TAGS():
        return [RiskManagement.NO_MANAGEMENT, RiskManagement.BE_AFTER_1R, RiskManagement.BE_AFTER_PUSH, RiskManagement.CLOSE_EARLY]
    
    def add_tags_to_trade(trade: Execution, management_strategy: str):
        if not trade.has_tag("management_strategy"):
            trade.add_tag("management_strategy", management_strategy)
    
    @staticmethod
    def CATEGORICAL_TAGS():
        return [RiskManagement.FEATURE_MANAGEMENT_STRATEGY]

class Outcome(BaseFeature):
    
    FEATURE_OUTCOME = "outcome"
    DEFAULT_OUTCOME = None
    TYPE_OUTCOME = str
    
    DEPENDENCY_RR = "rr"
    DEPENDS_ON = [DEPENDENCY_RR]

    # Outcome CATEGORIES
    WIN = "win"
    LOSS = "loss"
    BE_THESHOLD = 0.2
    BE = "be"
    FEATURE_OUTCOMECATEGORIES = [WIN, LOSS, BE]
    
    
    @classmethod
    def ALL_TAGS(cls):
        return [cls.FEATURE_OUTCOME]
    
    @staticmethod
    def get_outcome(rr: float) -> str:
        return Outcome.WIN if rr > 0 else (Outcome.BE if abs(rr) < Outcome.BE_THESHOLD else Outcome.LOSS)
    
    def add_tags_to_trade(trade: Execution):
        rr = next((t.value for t in trade.tags if t.key == Outcome.DEPENDENCY_RR), None)
        if not rr:
            logging.warning(f"Trade {trade.uid} does not have the '{Outcome.DEPENDENCY_RR}' tag")
        
        if rr is not None:
            trade.add_tag("outcome", Outcome.get_outcome(rr))
    
    def add_tags_to_df(df: pd.DataFrame):
        if not "rr" in df.columns:
            raise ValueError(f"DataFrame must have the '{Outcome.DEPENDS_ON}' columns")
        
        df[Outcome.FEATURE_OUTCOME] = df[Outcome.DEPENDENCY_RR].apply(lambda x: Outcome.get_outcome(x))
    
    @staticmethod
    def CATEGORICAL_TAGS():
        return [Outcome.FEATURE_OUTCOME]

class PositionAction:
    MARKET_ENTRY = "market_entry"
    LIMIT_ENTRY = "limit_entry"
    STOP_ENTRY = "stop_entry"
    MODIFY_POSITION = "modify_position"
    CLOSE_POSITION = "close_position"
    
    def __init__(self, action_type:str, ts: datetime):
        self.action_type = action_type
        self.ts = ts

from datetime import datetime
from dataclasses import field
import matplotlib.pyplot as plt
import time as t
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

class TradePosition(BaseFeature):
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

    def add_tags_to_trade(self, trade: Execution):
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
    
    @staticmethod
    def ALL_TAGS():
        return [TradePosition.TAG_ENTRY_PRICE, TradePosition.TAG_SL_PRICE, TradePosition.TAG_TP_PRICE, TradePosition.TAG_SL_DISTANCE, TradePosition.TAG_TP_DISTANCE, TradePosition.TAG_SIDE, TradePosition.TAG_RETURN]
    

    @staticmethod
    def IGNORED_TAGS():
        return [TradePosition.TAG_ENTRY_PRICE,TradePosition.TAG_SL_PRICE,TradePosition.TAG_TP_PRICE,TradePosition.TAG_SL_DISTANCE,
                TradePosition.TAG_TP_DISTANCE,TradePosition.TAG_RETURN]
    
    @staticmethod
    def CATEGORICAL_TAGS():
        return [TradePosition.TAG_SIDE]



class InitialReward(BaseFeature):
    TAG_RR = 'initial_risk_reward'
    TAG_RETURN = 'initial_return'
    

    @staticmethod
    def calculate_initial_risk_reward(entry_price: float, sl_price: float, tp_price: float) -> float:
        return (tp_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def calculate_initial_return(entry_price: float, tp_price: float) -> float:
        return tp_price - entry_price
    
    @staticmethod
    def add_tags_to_trade(trade: Execution):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        tp_price = next((t.value for t in trade.tags if t.key == "tp_price"), None)
        if entry_price is not None and sl_price is not None and tp_price is not None:
            rr = InitialReward.calculate_initial_risk_reward(entry_price, sl_price, tp_price)
            trade.add_tag("initial_risk_reward", rr)
            trade.add_tag("initial_return", InitialReward.calculate_initial_return(entry_price, tp_price))
    
    @staticmethod
    def ALL_TAGS():
        return [InitialReward.TAG_RR, InitialReward.TAG_RETURN]
    
    @staticmethod
    def FLOAT_TAGS():
        return [InitialReward.TAG_RR, InitialReward.TAG_RETURN]
    
    @staticmethod
    def DATETIME_TAGS():
        return [InitialReward.TAG_RETURN]

class PotentialReward(BaseFeature):
    TAG_RR = 'potential_risk_reward'
    TAG_RETURN = 'potential_return'
    TAG_PRICE = 'potential_price'
    
    @staticmethod
    def ALL_TAGS():
        return [PotentialReward.TAG_RR, PotentialReward.TAG_RETURN, PotentialReward.TAG_PRICE]
    
    @staticmethod
    def calculate_potential_risk_reward(entry_price: float, sl_price: float, potential_price: float) -> float:
        return (potential_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def calculate_potential_return(entry_price: float, potential_price: float) -> float:
        return potential_price - entry_price

    @staticmethod
    def add_tags_to_trade(trade: Execution, potential_price: float):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        if entry_price is not None and sl_price is not None:
            rr = PotentialReward.calculate_potential_risk_reward(entry_price, sl_price, potential_price)
            trade.add_tag("potential_risk_reward", rr)
            trade.add_tag("potential_return", PotentialReward.calculate_potential_return(entry_price, potential_price))
            trade.add_tag("potential_price", potential_price)
    
    @staticmethod
    def IGNORED_TAGS():
        return [PotentialReward.TAG_RR, PotentialReward.TAG_RETURN, PotentialReward.TAG_PRICE]

    @staticmethod
    def FLOAT_TAGS():
        return [PotentialReward.TAG_RR, PotentialReward.TAG_RETURN, PotentialReward.TAG_PRICE]

class EntryTime(BaseFeature):
    TAG_ENTRY_TIME = "entry_time"
    DEFAULT_ENTRY_TIME = None

    
    def __init__(self, entry_time: datetime):
        self.entry_time = entry_time
            
    def add_tags_to_trade(self, trade: Execution):
        if EntryTime.TAG_ENTRY_TIME not in trade.get_tags_dict():
            trade.add_tag("entry_time", self.entry_time)
        else:
            for tag in trade.tags:
                if tag.key == EntryTime.TAG_ENTRY_TIME:
                    tag.value = self.entry_time
                    break
    
        
    @staticmethod
    def ALL_TAGS():
        return [EntryTime.TAG_ENTRY_TIME]
    
    @staticmethod
    def IGNORED_TAGS():
        return [EntryTime.TAG_ENTRY_TIME]
    
    @staticmethod
    def DATETIME_TAGS():
        return [EntryTime.TAG_ENTRY_TIME]

class Sessions(BaseFeature):
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
    
    def add_tags_to_trade(ts: pd.Timestamp, trade: Execution):
        if ts is not None:
            session = Sessions.session_from_ts(ts)
            trade.add_tag("session", session)
    
    def add_tags_to_trade(trade: Execution):
        ts = next((t.value for t in trade.tags if t.key == EntryTime.TAG_ENTRY_TIME), None)
        if ts is not None:
            session = Sessions.session_from_ts(ts)
            trade.add_tag("session", session)
    
    @staticmethod
    def IGNORED_TAGS():
        return [Sessions.TAG_SESSION]
    
    @staticmethod
    def ALL_TAGS():
        return [Sessions.TAG_SESSION, Sessions.LONDON, Sessions.NEW_YORK, Sessions.TOKYO]
    
    @staticmethod
    def CATEGORICAL_TAGS():
        return [Sessions.TAG_SESSION]

class RR(BaseFeature):
    TAG_RR = "rr"
    DEFAULT_RR = 0.0
    
    @staticmethod
    def calculate_risk_reward_ratio(entry_price: float, sl_price: float, close_price: float) -> float:
        return (close_price - entry_price) / (entry_price - sl_price)
    
    @staticmethod
    def add_tags_to_trade(trade: Execution):
        entry_price = next((t.value for t in trade.tags if t.key == "entry_price"), None)
        sl_price = next((t.value for t in trade.tags if t.key == "sl_price"), None)
        close_price = next((t.value for t in trade.tags if t.key == "close_price"), None)
        prices = [entry_price, sl_price, close_price]
        
        if entry_price is not None and sl_price is not None and close_price is not None:
            rr = RR.calculate_risk_reward_ratio(entry_price, sl_price, close_price)
            trade.add_tag(RR.TAG_RR, rr)
        else:
            logging.warning(f'trade {trade.uid}: RR calculation failed. Some prices are missing: { dict(zip(["entry_price", "sl_price", "close_price"], prices)) }')
    
    @staticmethod
    def ALL_TAGS():
        return [RR.TAG_RR]
    
    @staticmethod
    def FLOAT_TAGS():
        return [RR.TAG_RR]

@dataclass
class Account(BaseFeature):
    DEFAULT = "default"
    TAG_ACCOUNT = 'account'

    @classmethod
    def ALL_TAGS(cls):
        return [cls.TAG_ACCOUNT]

    @classmethod
    def IGNORED_TAGS(cls):
        return [cls.TAG_ACCOUNT]
    
    @classmethod
    def CATEGORICAL_TAGS(cls):
        return [cls.TAG_ACCOUNT]

    @classmethod
    def add_to_trade(cls, trade: Execution, account_name: str):
        trade.add_tag(cls.TAG_ACCOUNT, account_name)

    @classmethod
    def sanity_check(cls, df: pd.DataFrame, threshold=1.0):
        accs = df[cls.TAG_ACCOUNT]
    
        logging.debug(accs)
        
        valid_count = accs.notna().sum()
        total_count = len(accs)
        valid_ratio = valid_count / total_count if total_count > 0 else 0
        
        if valid_ratio < threshold:
            cls._sanity_fail(f'valid_ratio={valid_ratio:.2f} to low (to many nans)')
        else:
            cls._sanity_ok()
        
        

def all_feature_classes() -> List[Type[Feature]]:
    return [Confidence, MultiTimeframeAnalysis, RiskManagement, Outcome, TradePosition, InitialReward, PotentialReward, EntryTime, Sessions, RR]


def get_all_ignored_tags() -> List[str]:
    ignored_tags = []
    classes = all_feature_classes()
    for cls in classes:
        ignored_tags.extend(cls.IGNORED_TAGS())
    return ignored_tags

def get_all_categorical_tags() -> List[str]:
    categorical_tags = []
    classes = all_feature_classes()
    for cls in classes:
        categorical_tags.extend(cls.CATEGORICAL_TAGS())
    return list(set(categorical_tags))

def get_all_float_tags() -> List[str]:
    float_tags = []
    classes = all_feature_classes()
    for cls in classes:
        float_tags.extend(cls.FLOAT_TAGS())
    return list(set(float_tags))

def get_all_datetime_tags() -> List[str]:
    datetime_tags = []
    classes = all_feature_classes()
    for cls in classes:
        datetime_tags.extend(cls.DATETIME_TAGS())
    return list(set(datetime_tags))

def used_feature_classes(df: pd.DataFrame) -> List[Type[Feature]]:
    used_classes = []
    for col in df.columns:
        for cls in all_feature_classes():
            for tag in cls.ALL_TAGS():
                if tag in col:
                    logging.debug(f"Found class {cls.__name__} via feature {tag} in column {col}")
                    used_classes.append(cls.__name__)
    
    return list(set(used_classes))

def used_feature_tags(df: pd.DataFrame) -> List[str]:
    used_tags = []
    for col in df.columns:
        for cls in all_feature_classes():
            for tag in cls.ALL_TAGS():
                if tag in col:
                    logging.info(f"Found tag {tag} in column {col}")
                    used_tags.append(tag)
    return list(set(used_tags))
