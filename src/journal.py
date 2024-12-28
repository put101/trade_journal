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

journal = TradeJournal()

t = Trade(uid="1")
t.add_tag(PA.type_1_(TF.m1), True)
t.add_tag(TYPE_3_M15, True)
journal.add_trade(t.copy())

t = Trade(uid="2")
t.add_tag(PA.type_2_(TF.h1), True)
journal.add_trade(t)

# Example of adding a numeric tag
t = Trade(uid="3")
t.add_tag("SL_distance", 0.5)
journal.add_trade(t)

# Copy trade and modify for a new data point
t_copy = t.copy()
t_copy.uid = "4"
t_copy.add_tag("management_strategy", "strategy_2")
journal.add_trade(t_copy)

print(journal.trades)
