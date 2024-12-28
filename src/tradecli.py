from dataclasses import dataclass, field
from typing import List, Dict, Union
import pandas as pd
from datetime import datetime
import os
import copy
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class Tag:
    timestamp: datetime
    key: str
    value: Union[bool, float]

@dataclass
class Trade:
    uid: str
    tags: List[Tag] = field(default_factory=list)

    def get_tags_dict(self) -> Dict[str, any]:
        return {tag.key: tag.value for tag in self.tags}
    
    def add_tag(self, key: str, value: Union[bool, float]):
        self.tags.append(Tag(key=key, value=value, timestamp=None))

    def copy(self):
        return copy.deepcopy(self)


@dataclass
class TradeJournal:
    trades: List[Trade] = field(default_factory=list)

    def add_trade(self, trade: Trade):
        self.trades.append(trade)

    def to_dataframe(self) -> pd.DataFrame:
        data = []
        all_tags = set(tag.key for trade in self.trades for tag in trade.tags)
        for trade in self.trades:
            row = {'trade_uid': trade.uid}
            for tag in all_tags:
                tag_value = next((t.value for t in trade.tags if t.key == tag), None)
                row[tag] = tag_value
            data.append(row)
        return pd.DataFrame(data)

    def get_simple_statistics(self) -> str:
        df = self.to_dataframe()
        if df.empty:
            return "No trades found."
        trade_count = df['trade_uid'].nunique()
        
        n_long = df[df['side'] == 'long'].shape[0]
        n_short = df[df['side'] == 'short'].shape[0]
        
        return f"Trade count: {trade_count}\nLong trades: {n_long}\nShort trades: {n_short}"

    def write_index_markdown(self, output_dir: str):
        index_path = os.path.join(output_dir, "index.md")
        stats = self.get_simple_statistics()
        lines = [
            "# Trade Journal Index",
            "## Summary Statistics",
            stats,
            "## Trades"
        ]
        for trade in self.trades:
            lines.append(f"- [Trade {trade.uid}](trade_{trade.uid}.md)")
        with open(index_path, 'w') as index_file:
            index_file.write("\n".join(lines))

    def to_markdown(self, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for trade in self.trades:
            md_path = os.path.join(output_dir, f"trade_{trade.uid}.md")
            md_content = f"# Trade Summary\n\n"
            md_content += f"**Trade UID:** {trade.uid}\n"
            md_content += f"**Tags:** {', '.join([f'{tag.key}:{tag.value}' for tag in trade.tags])}\n"
            stats = self.get_simple_statistics()
            md_content += f"\n## Overall Statistics\n{stats}\n"
            md_content += "\n[Back to Index](index.md)\n"
            with open(md_path, 'w') as md_file:
                md_file.write(md_content)
        self.write_index_markdown(output_dir)
