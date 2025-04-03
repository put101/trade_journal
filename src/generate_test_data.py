from datetime import datetime, timedelta
import random
import pandas as pd
from src.journal import TradeJournal, Execution, TradePosition, EntryTime, RR, Outcome, MultiTimeframeAnalysis, Confidence, RiskManagement, PA, Account, Sessions, InitialReward


def get_test_data_journal() -> TradeJournal:
    journal = TradeJournal()
    confidence_levels = [1, 2, 3, 4, 5]
    management_strategies = [RiskManagement.NO_MANAGEMENT, RiskManagement.BE_AFTER_1R, RiskManagement.BE_AFTER_PUSH, RiskManagement.CLOSE_EARLY]
    timeframes = PA.ALL_TAGS()

    for i in range(5, 15):
        t = Execution(uid=str(1000+i))
        t.add_tag(random.choice([PA.type_1_(tf) for tf in timeframes]), True)
        t.add_tag(random.choice([PA.type_2_(tf) for tf in timeframes]), True)
        t.add_tag(random.choice([PA.type_3_(tf) for tf in timeframes]), True)
        t.add_tag("unit_test", True)
        Account.add_account_to_trade(t, "test_account")

        entry_price = round(1.1000 + random.uniform(0.01, 0.05), 4)
        is_long = random.choice([True, False])
        rr = random.uniform(1, 10.0)
        WR = 0.7
        SL_POINTS = 0.005
        is_win = random.choices([True, False], weights=[WR, 1-WR], k=1)[0]
        actual_rr = random.uniform(0, 10.0) if is_win else random.uniform(-1.50, 0)
        actual_rr = round(actual_rr, 2)

        if is_long:
            sl_price = entry_price - SL_POINTS
            tp_price = entry_price + SL_POINTS * rr
            close_price = entry_price + SL_POINTS * actual_rr
        else:
            sl_price = entry_price + SL_POINTS
            tp_price = entry_price - SL_POINTS * rr
            close_price = entry_price - SL_POINTS * actual_rr

        position = TradePosition(entry_price=entry_price, sl_price=sl_price, tp_price=tp_price, close_price=close_price)
        position.add_tags_to_trade(t)
        hour = random.normalvariate(9, 1)
        minute = random.choice([0, 15, 30, 45])
        minute = random.normalvariate(minute, 15)
        entry_time = pd.Timestamp.now() + pd.Timedelta(days=random.randint(-30, 0), hours=hour, minutes=minute)
        EntryTime(entry_time=entry_time).add_tags_to_trade(t)
        RR.add_tags_to_trade(t)
        Outcome.add_tags_to_trade(t)
        MultiTimeframeAnalysis.add_tags_to_trade(t, random.choice([True, False]))
        Confidence.add_tags_to_trade(t, random.choice(confidence_levels))
        RiskManagement.add_tags_to_trade(t, random.choice(management_strategies))

        journal.add_trade(t)

    return journal 