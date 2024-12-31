from typing import List
from datetime import datetime
import pandas as pd

class Trade:
    def __init__(self, uid: str):
        self.uid = uid
        self.tags = []

    def add_tag(self, key: str, value):
        self.tags.append(Tag(key, value))

    def has_tag(self, key: str) -> bool:
        return any(tag.key == key for tag in self.tags)

    def get_tags_dict(self):
        return {tag.key: tag.value for tag in self.tags}

    def copy(self):
        new_trade = Trade(self.uid)
        new_trade.tags = self.tags.copy()
        return new_trade

class TradeJournal:
    def __init__(self):
        self.trades = []

    def add_trade(self, trade: Trade):
        self.trades.append(trade)

    def to_dataframe(self) -> pd.DataFrame:
        data = []
        for trade in self.trades:
            trade_data = trade.get_tags_dict()
            trade_data['uid'] = trade.uid
            data.append(trade_data)
        return pd.DataFrame(data)

class Tag:
    def __init__(self, key: str, value):
        self.key = key
        self.value = value
