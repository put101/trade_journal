from datetime import datetime
import markdown
import os
import random
import logging
import re  # Add regex module for pattern matching
import scipy
from src.tradecli import * 
from src.features import *

logging.basicConfig(level=logging.INFO)


j = TradeJournal()
j.get_all_categorical_tags = get_all_categorical_tags
j.get_all_ignored_tags = get_all_ignored_tags

### TEST DATA START

# Define distributions for different tags
confidence_levels = [1, 2, 3, 4, 5]
management_strategies = [RiskManagement.NO_MANAGEMENT, RiskManagement.BE_AFTER_1R, RiskManagement.BE_AFTER_PUSH, RiskManagement.CLOSE_EARLY]
timeframes = TF.ALL_TAGS


USE_TEST_DATA = True

logging.info("Adding more trades to the journal")
# Add more entries to the journal using a loop with random choices
for i in range(5, 15):
    t = Trade(uid=str(1000+i))
    t.add_tag(random.choice([PA.type_1_(tf) for tf in timeframes]), True)
    t.add_tag(random.choice([PA.type_2_(tf) for tf in timeframes]), True)
    t.add_tag(random.choice([PA.type_3_(tf) for tf in timeframes]), True)
    t.add_tag("unit_test", True)  # Add unit_test tag
    Account.add_account_to_trade(t, "test_account")  # Add account tag
    
    if USE_TEST_DATA:
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
    position = TradePosition(entry_price=entry_price, sl_price=sl_price, tp_price=tp_price, close_price=close_price)
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

DF_PRE = j.to_dataframe().copy()

for trade in j.trades:
    Sessions.add_tags_to_trade(trade)
    RR.add_tags_to_trade(trade)
    InitialReward.add_tags_to_trade(trade)
    # DEFAULTS
    RiskManagement.add_tags_to_trade(trade, RiskManagement.NO_MANAGEMENT)
    # set False for the PA tags that are not set
    
    for tag in PA.ALL_TAGS():
        if not trade.has_tag(tag):
            # trade.add_tag(tag, False)
            pass

def get_full_df():
    return j.to_dataframe().copy()

POST_DF = get_full_df().copy()

get_number_of_trades = lambda df: len(df)
get_set_of_tags = lambda df: frozenset([tag for tag in df.columns if tag != "uid"])
get_number_of_tags = lambda df: len(get_set_of_tags(df))
get_number_of_trades_with_tag = lambda df, tag: len(df[df[tag].notnull()])


# debug
print(t4)