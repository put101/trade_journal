from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime
import os

EXECUTION_ID_COUNTER = 0

@dataclass
class Action:
    timestamp: datetime
    description: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Execution:
    rr: float
    entry_price: float
    stop_loss: float
    take_profit: float
    account: str = "default"
    actions: List[Action] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    numeric_tags: Dict[str, float] = field(default_factory=dict)
    quantity: float = 1.0
    uid: int = field(init=False)
    trade: "Trade" = field(init=False)

    def go_break_even(self):
        self.stop_loss = self.entry_price
        self.tags['status'] = 'BE'

    def scale_in(self, additional_quantity: float, price: float):
        self.quantity += additional_quantity
        self.tags['scaled_in'] = 'true'

    def scale_out(self, partial_quantity: float):
        if partial_quantity >= self.quantity:
            partial_quantity = self.quantity
        self.quantity -= partial_quantity
        self.tags['scaled_out'] = 'true'

@dataclass
class Trade:
    uid: str
    tags: List[str] = field(default_factory=list)
    numeric_tags: Dict[str, float] = field(default_factory=dict)
    executions: List[Execution] = field(default_factory=list)
    execution_id_counter: int = field(default=0, init=False)

    def add_execution(self, execution: Execution):
        self.execution_id_counter += 1
        execution.uid = self.execution_id_counter
        execution.trade = self
        self.executions.append(execution)

@dataclass
class TradeJournal:
    trades: List[Trade] = field(default_factory=list)

    def add_trade(self, trade: Trade):
        self.trades.append(trade)

    def add_execution_to_trade(self, trade: Trade, execution: Execution):
        trade.add_execution(execution)

    def add_action_to_execution(self, execution: Execution, action: Action):
        execution.actions.append(action)
        if action.description == 'go_break_even':
            execution.go_break_even()
    
    def to_dataframe(self) -> pd.DataFrame:
        data = []
        for trade in self.trades:
            for execution in trade.executions:
                row = {
                    'execution_uid': execution.uid,
                    'trade_uid': trade.uid,
                    'rr': execution.rr,
                    'entry_price': execution.entry_price,
                    'stop_loss': execution.stop_loss,
                    'take_profit': execution.take_profit,
                    'trade_tags': ','.join(trade.tags),
                    **trade.numeric_tags,
                    **execution.tags,
                    **execution.numeric_tags
                }
                data.append(row)
        return pd.DataFrame(data)


    def read_assets_and_create_markdown(self, assets_dir: str, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        assets_subfolder = os.path.join(output_dir, "generated_assets")
        if not os.path.exists(assets_subfolder):
            os.makedirs(assets_subfolder)
        for filename in os.listdir(assets_dir):
            if filename.endswith(".txt"):  # Assuming the assets are text files
                with open(os.path.join(assets_dir, filename), 'r') as file:
                    content = file.read()
                    md_content = markdown.markdown(content)
                    output_filename = os.path.join(assets_subfolder, f"{os.path.splitext(filename)[0]}.md")
                    with open(output_filename, 'w') as md_file:
                        md_file.write(md_content)


    def get_simple_statistics(self) -> str:
        df = self.to_dataframe()
        if df.empty:
            return "No trades or executions found."
        trade_count = df['trade_uid'].nunique()
        avg_rr = df['rr'].mean()
        return f"Trade count: {trade_count}, Average RR: {avg_rr:.2f}"

    def write_index_markdown(self, output_dir: str):
        import matplotlib.pyplot as plt
        index_path = os.path.join(output_dir, "index.md")
        stats = self.get_simple_statistics()
        df = self.to_dataframe()
        df['rr'].hist()
        plt.savefig(os.path.join(output_dir, "summary_plot.png"))
        lines = [
            "# Trade Journal Index",
            "## Summary Statistics",
            stats,
            "## Summary Plot",
            "![Summary Plot](summary_plot.png)",
            "## Trades"
        ]
        for trade_id in df['trade_uid'].unique():
            lines.append(f"- Trade {trade_id}")
        with open(index_path, 'w') as index_file:
            index_file.write("\n".join(lines))

    def to_markdown(self, output_dir: str):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for trade in self.trades:
            for execution in trade.executions:
                md_path = os.path.join(output_dir, f"execution_{execution.uid}.md")
                md_content = f"# Trade Summary\n\n"
                md_content += f"**Execution UID:** {execution.uid}\n"
                md_content += f"**Trade UID:** {trade.uid}\n"
                md_content += f"**RR:** {execution.rr}\n"
                md_content += f"**Entry Price:** {execution.entry_price}\n"
                md_content += f"**Stop Loss:** {execution.stop_loss}\n"
                md_content += f"**Take Profit:** {execution.take_profit}\n"
                md_content += f"**Trade Tags:** {', '.join(trade.tags)}\n"
                md_content += f"**Execution Tags:** {', '.join(execution.tags.keys())}\n"
                md_content += f"**Numeric Tags:** {execution.numeric_tags}\n"
                stats = self.get_simple_statistics()
                md_content += f"\n## Overall Statistics\n{stats}\n"
                md_content += "\n[Back to Index](index.md)\n"
                with open(md_path, 'w') as md_file:
                    md_file.write(md_content)
        self.write_index_markdown(output_dir)
