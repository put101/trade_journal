#!/usr/bin/env python3

import click
import yaml
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Constants
TRADES_DIR = Path("trades")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Trade:
    def __init__(self, identifier, entry_ts, symbol, lots, risk, account, balance, tags=None, planned_rr=None, actual_rr=None, theoretical_rr=None, outcome=None, entry_price=0, sl_pips=0, tp_pips=0):
        self.identifier = identifier
        self.entry_ts = entry_ts
        self.symbol = symbol
        self.lots = lots
        self.risk = risk
        self.account = account
        self.balance = balance
        self.tags = tags if tags is not None else []
        self.planned_rr = planned_rr
        self.actual_rr = actual_rr
        self.theoretical_rr = theoretical_rr
        self.outcome = outcome
        self.entry_price = entry_price
        self.sl_pips = sl_pips
        self.tp_pips = tp_pips

    def __repr__(self):
        return (f"Trade(identifier={self.identifier}, entry_ts={self.entry_ts}, symbol={self.symbol}, "
                f"lots={self.lots}, risk={self.risk}, account={self.account}, balance={self.balance}, "
                f"tags={self.tags}, planned_rr={self.planned_rr}, actual_rr={self.actual_rr}, "
                f"theoretical_rr={self.theoretical_rr}, outcome={self.outcome}, entry_price={self.entry_price}, "
                f"sl_pips={self.sl_pips}, tp_pips={self.tp_pips})")

    def to_yaml(self):
        return yaml.dump(self, default_flow_style=False)

class TradeBuilder:
    def __init__(self):
        self.identifier = None
        self.entry_ts = datetime.now().isoformat()
        self.symbol = None
        self.lots = 0
        self.risk = 0
        self.account = None
        self.balance = 0
        self.entry_price = 0
        self.sl_pips = 0
        self.tp_pips = 0
        self.sl_price = 0
        self.tp_price = 0
        self.tags = []
        self.planned_rr = None
        self.actual_rr = None
        self.theoretical_rr = None
        self.outcome = None

    def set_identifier(self, identifier):
        self.identifier = identifier
        return self

    def set_symbol(self, symbol):
        self.symbol = symbol
        return self

    def set_lots(self, lots):
        self.lots = lots
        return self

    def set_risk(self, risk):
        self.risk = risk
        return self

    def set_account(self, account):
        self.account = account
        return self

    def set_balance(self, balance):
        self.balance = balance
        return self

    def set_entry_price(self, entry_price):
        self.entry_price = entry_price
        return self

    def set_sl_pips(self, sl_pips):
        self.sl_pips = sl_pips
        self.sl_price = self.entry_price - (sl_pips * 0.0001)
        return self

    def set_tp_pips(self, tp_pips):
        self.tp_pips = tp_pips
        self.tp_price = self.entry_price + (tp_pips * 0.0001)
        return self

    def set_tags(self, tags):
        self.tags = tags
        return self

    def set_planned_rr(self, planned_rr):
        self.planned_rr = planned_rr
        return self

    def set_actual_rr(self, actual_rr):
        self.actual_rr = actual_rr
        return self

    def set_theoretical_rr(self, theoretical_rr):
        self.theoretical_rr = theoretical_rr
        return self

    def set_outcome(self, outcome):
        self.outcome = outcome
        return self

    def calculate_risk(self):
        if self.sl_pips > 0 and self.lots > 0 and self.balance > 0:
            self.risk = (self.sl_pips * self.lots * 10) / self.balance * 100
        else:
            logger.warning("Risk calculation skipped due to zero values in sl_pips, lots, or balance.")
        return self

    def calculate_planned_rr(self):
        if self.tp_pips > 0 and self.sl_pips > 0:
            self.planned_rr = self.tp_pips / self.sl_pips
        else:
            logger.warning("Planned RR calculation skipped due to zero values in tp_pips or sl_pips.")
        return self

    def calculate_actual_rr(self):
        if self.outcome is not None and self.risk != 0:
            self.actual_rr = self.outcome / self.risk
        else:
            logger.warning("Actual RR calculation skipped due to zero risk or missing outcome.")
        return self

    def calculate_theoretical_rr(self):
        if self.tp_price > 0 and self.sl_price > 0 and self.entry_price > 0 and (self.entry_price - self.sl_price) != 0:
            self.theoretical_rr = (self.tp_price - self.entry_price) / (self.entry_price - self.sl_price)
        else:
            logger.warning("Theoretical RR calculation skipped due to zero values in tp_price, sl_price, or entry_price.")
        return self

    def calculate_outcome(self):
        if self.actual_rr is not None and self.risk != 0:
            self.outcome = self.actual_rr * self.risk
        else:
            logger.warning("Outcome calculation skipped due to zero risk or missing actual RR.")
        return self

    def build(self):
        self.calculate_risk()
        self.calculate_planned_rr()
        self.calculate_actual_rr()
        self.calculate_theoretical_rr()
        self.calculate_outcome()
        return Trade(self.identifier, self.entry_ts, self.symbol, self.lots, self.risk, self.account, self.balance, self.tags, self.planned_rr, self.actual_rr, self.theoretical_rr, self.outcome, self.entry_price, self.sl_pips, self.tp_pips)

def ensure_trades_dir():
    TRADES_DIR.mkdir(exist_ok=True)

def save_trade(trade):
    file_path = TRADES_DIR / f"trade_{trade.identifier}.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(trade, f, default_flow_style=False)

def load_trade(file_path):
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def get_trade_files():
    ensure_trades_dir()
    return [str(file) for file in TRADES_DIR.glob("trade_*.yaml")]

def trade_constructor(loader, node):
    values = loader.construct_mapping(node)
    return Trade(**values)

# Register the Trade class with PyYAML
yaml.add_representer(Trade, lambda dumper, data: dumper.represent_mapping('!Trade', data.__dict__))
yaml.add_constructor('!Trade', trade_constructor)

load_dotenv()

# Set JOURNAL_ROOT to the project root for development
JOURNAL_ROOT = os.getenv('JOURNAL_ROOT', str(Path(__file__).resolve().parent.parent))

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose mode')
@click.pass_context
def cli(ctx, verbose):
    """Trading Journal CLI - Manage your trades efficiently."""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Journal root folder is: {JOURNAL_ROOT}")

@cli.command()
@click.option('-i', '--identifier', required=True, help='Trade identifier')
@click.option('-s', '--symbol', required=True, help='Trading symbol/pair')
@click.option('-l', '--lots', type=float, required=True, help='Number of lots')
@click.option('-r', '--risk', type=float, required=True, help='Risk percentage')
@click.option('-a', '--account', required=True, help='Account name')
@click.option('-b', '--balance', type=float, required=True, help='Account balance')
@click.option('-t', '--tags', multiple=True, help='Tags for the trade')
@click.pass_context
def add_full(ctx, identifier, symbol, lots, risk, account, balance, tags):
    """Add a new trade entry with full specification."""
    ensure_trades_dir()
    trade = Trade(identifier, datetime.now().isoformat(), symbol, lots, risk, account, balance, list(tags))
    save_trade(trade)
    if ctx.obj['VERBOSE']:
        logger.info(f"Trade added with ID: {identifier}")

@cli.command()
@click.option('-i', '--identifier', required=True, help='Trade identifier')
@click.option('-s', '--symbol', required=True, help='Trading symbol/pair')
@click.option('-l', '--lots', type=float, required=True, help='Number of lots')
@click.option('-e', '--entry_price', type=float, required=True, help='Entry price')
@click.option('--sl', '--sl_pips', 'sl_pips', type=float, required=True, help='Stop loss in pips')
@click.option('--tp', '--tp_pips', 'tp_pips', type=float, required=True, help='Take profit in pips')
@click.option('-a', '--account', required=True, help='Account name')
@click.option('-b', '--balance', type=float, required=True, help='Account balance')
@click.option('-t', '--tags', multiple=True, help='Tags for the trade')
@click.option('--planned_rr', type=float, help='Planned risk-reward ratio')
@click.option('--actual_rr', type=float, help='Actual risk-reward ratio')
@click.option('--theoretical_rr', type=float, help='Theoretical risk-reward ratio')
@click.option('--outcome', type=float, help='Monetary outcome')
@click.option('--calculate', is_flag=True, help='Calculate and persist the trade with derived metrics')
@click.pass_context
def add_builder(ctx, identifier, symbol, lots, entry_price, sl_pips, tp_pips, account, balance, tags, planned_rr, actual_rr, theoretical_rr, outcome, calculate):
    """Add a new trade entry using the builder pattern."""
    ensure_trades_dir()
    trade_builder = (TradeBuilder()
                     .set_identifier(identifier)
                     .set_symbol(symbol)
                     .set_lots(lots)
                     .set_entry_price(entry_price)
                     .set_sl_pips(sl_pips)
                     .set_tp_pips(tp_pips)
                     .set_account(account)
                     .set_balance(balance)
                     .set_tags(list(tags))
                     .set_planned_rr(planned_rr)
                     .set_actual_rr(actual_rr)
                     .set_theoretical_rr(theoretical_rr)
                     .set_outcome(outcome))
    
    if calculate:
        trade_builder.calculate_risk().calculate_planned_rr().calculate_actual_rr().calculate_theoretical_rr().calculate_outcome()
    
    trade = trade_builder.build()
    save_trade(trade)
    if ctx.obj['VERBOSE']:
        logger.info(f"Trade added with ID: {identifier}")

@cli.command(name='list')
@click.option('-v', '--verbose', is_flag=True, help='Show full trade details')
@click.pass_context
def list_command(ctx, verbose):
    """List all trades."""
    trades = []
    for file in get_trade_files():
        trade = load_trade(file)
        trades.append(trade)
    
    trades.sort(key=lambda x: x.entry_ts, reverse=True)
    
    for trade in trades:
        if verbose or ctx.obj['VERBOSE']:
            logger.info(repr(trade))
        else:
            logger.info(f"ID: {trade.identifier} | Symbol: {trade.symbol} | Lots: {trade.lots} | Entry TS: {trade.entry_ts} | Tags: {', '.join(trade.tags)}")

@cli.command()
@click.argument('identifier')
@click.pass_context
def show(ctx, identifier):
    """Show details of a specific trade."""
    trade_file = TRADES_DIR / f"trade_{identifier}.yaml"
    if trade_file.exists():
        trade = load_trade(trade_file)
        logger.info(trade.to_yaml())
    else:
        logger.error(f"Trade with ID {identifier} not found.")

@cli.command()
@click.argument('identifier')
@click.option('--calculate', is_flag=True, help='Calculate and update the trade with derived metrics')
@click.pass_context
def update_trade(ctx, identifier, calculate):
    """Update an existing trade with calculated metrics."""
    trade_file = TRADES_DIR / f"trade_{identifier}.yaml"
    if trade_file.exists():
        try:
            trade = load_trade(trade_file)
            trade_builder = (TradeBuilder()
                             .set_identifier(trade.identifier)
                             .set_symbol(trade.symbol)
                             .set_lots(trade.lots)
                             .set_entry_price(getattr(trade, 'entry_price', 0))
                             .set_sl_pips(getattr(trade, 'sl_pips', 0))
                             .set_tp_pips(getattr(trade, 'tp_pips', 0))
                             .set_account(trade.account)
                             .set_balance(trade.balance)
                             .set_tags(trade.tags)
                             .set_planned_rr(trade.planned_rr)
                             .set_actual_rr(trade.actual_rr)
                             .set_theoretical_rr(trade.theoretical_rr)
                             .set_outcome(trade.outcome))
            print(trade_builder.build())
            if calculate:
                trade_builder.calculate_risk().calculate_planned_rr().calculate_actual_rr().calculate_theoretical_rr().calculate_outcome()
            
            updated_trade = trade_builder.build()
            save_trade(updated_trade)
            if ctx.obj['VERBOSE']:
                logger.info(f"Trade with ID: {identifier} updated.")
        except AttributeError as e:
            logger.error(f"Error updating trade with ID {identifier}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            if ctx.obj['VERBOSE']:
                raise
    else:
        logger.error(f"Trade with ID {identifier} not found.")

# Add alias for the list command
cli.add_command(list_command, name='l')

if __name__ == '__main__':
    cli()