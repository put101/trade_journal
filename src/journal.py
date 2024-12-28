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
    def type_1_(tf: str):
        return f'type_1_{tf}'
    def type_2_(tf:str):
        return f'type_2_{tf}'
    def type_3_(tf:str):
        return f'type_3_{tf}'
    
TYPE_3_M15 = PA.type_3_(TF.m15)
        
ALL_TAGS = frozenset(TF.ALL_TAGS + [PA.type_1_(tf) for tf in TF.ALL_TAGS] + [PA.type_2_(tf) for tf in TF.ALL_TAGS])
print(ALL_TAGS)

class TradePosition:
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

journal = TradeJournal()

t = Trade(uid="1")
t.add_tag(PA.type_1_(TF.m1), True)
t.add_tag(TYPE_3_M15, True)
journal.add_trade(t)
position = TradePosition(trade_uid="1", entry_price=1.1000, sl_price=1.0950, tp_price=1.1100)
position.add_tags_to_trade(t)

t = Trade(uid="2")
t.add_tag(PA.type_2_(TF.h1), True)
journal.add_trade(t)
position = TradePosition(trade_uid="2", entry_price=1.2000, sl_price=1.1950, tp_price=1.2100)
position.add_tags_to_trade(t)

t = Trade(uid="3")
t.add_tag("SL_distance", 0.5)
journal.add_trade(t)
position = TradePosition(trade_uid="3", entry_price=1.3000, sl_price=1.2950, tp_price=1.3100)
position.add_tags_to_trade(t)

t_copy = t.copy()
t_copy.uid = "4"
t_copy.add_tag("management_strategy", "strategy_2")
journal.add_trade(t_copy)
position = TradePosition(trade_uid="4", entry_price=1.3000, sl_price=1.2950, tp_price=1.3100, close_price=1.3050)
position.add_tags_to_trade(t_copy)

print(journal.trades)
