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
        
    def has_tag(self, key: str) -> bool:
        return any(tag.key == key for tag in self.tags)

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
        n_side_nans = df['side'].isnull().sum()
        
        winrate = df[df['outcome'] == 'win'].shape[0] / trade_count * 100
        n_outcome_nans = df['outcome'].isnull().sum()
        
        total_rows = df.shape[0]
        nans = df.isnull().sum().sum()
        
        # Calculate trade expectancy
        trade_expectancy = df['return'].mean()
        n_return_nans = df['return'].isnull().sum()
        
        return (f"Trade count: {trade_count}\n\n"
                f"Long trades: {n_long} (NaNs: {n_side_nans})\n\n"
                f"Short trades: {n_short} (NaNs: {n_side_nans})\n\n"
                f"Winrate: {winrate:.2f}% (NaNs: {n_outcome_nans})\n\n"
                f"Trade expectancy: {trade_expectancy:.2f} (NaNs: {n_return_nans})\n\n"
                f"Total rows: {total_rows}\n\n"
                f"NaNs or skipped values: {nans}")

    def get_tags_statistics(self) -> pd.DataFrame:
        df = self.to_dataframe()
        if df.empty:
            return pd.DataFrame()
        tags = [col for col in df.columns if col != 'trade_uid']
        tag_data = []
        for tag in tags:
            tag_data.append({
                'tag': tag,
                'count': df[tag].count(),
                'unique_values': df[tag].nunique(),
                'missing_values': df[tag].isnull().sum(),
                'most_common': df[tag].mode().values[0] if not df[tag].mode().empty else None,
                'most_common_freq': df[tag].mode().count() / df[tag].count() if df[tag].count() > 0 else None
            })
        return pd.DataFrame(tag_data)

    def plot_statistics(self, output_dir: str):
        df = self.to_dataframe()
        if df.empty:
            return
        
        total_rows = df.shape[0]
        skipped_rows_outcome = df['outcome'].isnull().sum()
        skipped_rows_return = df['return'].isnull().sum()
        
        plt.figure(figsize=(10, 6))
        sns.countplot(x='outcome', data=df)
        plt.title(f'Trade Outcomes (Total rows: {total_rows}, Skipped rows: {skipped_rows_outcome})')
        plt.xlabel('Outcome')
        plt.ylabel('Count')
        plt.savefig(os.path.join(output_dir, 'trade_outcomes.png'))
        plt.close()

        plt.figure(figsize=(10, 6))
        sns.histplot(df['return'].dropna(), kde=True)
        plt.title(f'Return Distribution (Total rows: {total_rows}, Skipped rows: {skipped_rows_return})')
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.savefig(os.path.join(output_dir, 'return_distribution.png'))
        plt.close()

    def write_index_markdown(self, output_dir: str):
        index_path = os.path.join(output_dir, "index.md")
        stats = self.get_simple_statistics()
        df = self.to_dataframe()
        lines = [
            "# Trade Journal Index",
            "## Summary Statistics",
            stats,
            "## Tags Analysis",
            "### Tags Statistics",
            self.get_tags_statistics().to_markdown(index=False),
            "### Tags Distribution",
            self.to_dataframe().describe().to_markdown(index=False),
            "## Trades",
            "![Trade Outcomes](trade_outcomes.png)",
            "This plot shows the distribution of trade outcomes (win/loss).",
            "![Return Distribution](return_distribution.png)",
            "This plot shows the distribution of returns for the trades. The histogram provides a visual representation of the frequency of different return values.",
            "## DataFrame",
            df.to_markdown(index=False)
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
            md_content += f"**Trade UID:** {trade.uid} \n\n"
            md_content += f"**Tags:** {', '.join([f'{tag.key}:{tag.value}' for tag in trade.tags])}\n\n"
            
            #md_content += f"\n\n![Trade Plot](trade_plot_{trade.uid}.png)\n\n"
                        
            md_content += f"## Trade Plot Explanation\n\n"

            md_content += "\n[Back to Index](index.md)\n"
            
            with open(md_path, 'w') as md_file:
                md_file.write(md_content)
            
        self.write_index_markdown(output_dir)
        self.plot_statistics(output_dir)

