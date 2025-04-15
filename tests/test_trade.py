import pytest
from datetime import datetime
from trade_old import *
import pandas as pd
from pandas import Timestamp



@pytest.fixture
def sample_trade_single() -> Execution:
    trade = Execution(entry_price=100, entry_time=Timestamp("2024-01-01 10:00"), sl_price=95, tp_price=110, size=1, sl_monetary_value=-100, side=CONST_BUY)
    return trade

@pytest.fixture
def sample_trade() -> Execution:
    trade = Execution(entry_price=100, entry_time=Timestamp("2024-01-01 10:00"), sl_price=95, tp_price=110, size=1, sl_monetary_value=-100, side=CONST_BUY)
    trade.add_position(102, 0.5, Timestamp("2024-01-01 15:00"))
    return trade


def test_initial_position(sample_trade):
    summary = sample_trade.get_trade_summary()
    assert summary["avg_entry_price"] == pytest.approx((100*1.0 + 102*0.5)/1.5)
    assert summary["total_size"] == 1.5
    
    for p in sample_trade.positions:
        keys = p.to_dict().keys()
        
        for k in ['side', 'size']:
            assert k in keys
        

def test_point_value(sample_trade):
    pv1 = sample_trade.point_value
    pv2 = Execution.calc_point_value(-100, abs(100-95), 1)
    pv3 = (100.0 / 5.0) * 1.0
    
    assert pv1==pv2
    assert pv2==pv3
    
    assert pv1 > 0 
    

