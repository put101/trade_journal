# src/journal.py
"""
This file is used to define some rudimentray functions for test data and also the actual journal with real data.

The main goal is to use the features.py file to define features step by step for each trade and then do little to no changes afterwards, besides maybe adding 
new features afterwards. The trades are then stored in a journal, which is simply a list of trades.
The journal supports going over all the trades and creating a feature dataframe for further analysis.

"""

import markdown
import os
import random
import logging
import re  # Add regex module for pattern matching
import scipy
from src.tradecli import * 
from src.features import *
from src.generate_test_data import get_test_data_journal
import trade

logging.basicConfig(level=logging.INFO)

# TRADING ACCOUNTS
ACC_IDEAL = "ideal"
ACC_MT5_VANTAGE = "mt5_vantage"
ACC_TEST = "test_account"

# TIMEFRAMES
TYPE_3_M15 = PA.type_3_(TF.m15)

j = TradeJournal()
j.get_all_categorical_tags = get_all_categorical_tags
j.get_all_ignored_tags = get_all_ignored_tags



t1 = None #TODO
t2 = DataPoint(uid="2")
t2.add_tag('taken', True)
Account.add_to_trade(t2, ACC_MT5_VANTAGE)
EntryTime(pd.Timestamp('2025-02-18 14:10:00')).add_tags_to_trade(t2)
TradePosition(entry_price=2914.03,sl_price=2910.94, tp_price=3000.0, close_price=None).add_tags_to_trade(t2)

print(t2)
j.add_trade(t2)

t4 = DataPoint(uid="4")
Account.add_to_trade(t4, ACC_IDEAL)
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
    Outcome.add_tags_to_trade(trade)
    # set False for the PA tags that are not set
    POI.add_tags(trade, [POI.DEFAULT_POI])
    
    for tag in PA.ALL_TAGS():
        if not trade.has_tag(tag):
            # trade.add_tag(tag, False)
            pass

def get_full_df():
    return j.to_dataframe().copy()

POST_DF = get_full_df().copy()
