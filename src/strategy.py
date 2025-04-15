import logging
from src.tradecli import Trade, TradeJournal
import pandas as pd
from pprint import pprint as pp
import utils


class StrategyV1():
    def __init__(self) -> None:
        pass
    
    def sanity_check(self, df: pd.DataFrame):
        """Check for required columns in the DataFrame."""
        must_have_cols = set(['entry_time', 'rr', 'outcome', 'htf_poi_ltf_confirmation'])
        
        cols = set(df.columns)

        # Check for missing columns
        missing_cols = must_have_cols - cols
        if missing_cols:
            logging.warning(f"Missing required columns: {missing_cols}")
        else:
            utils.ok('StrategyV1')


def sanity_checks(df: pd.DataFrame, jr: TradeJournal):
    """Perform general sanity checks on the trade journal and DataFrame.
    
    Checks include:
        - Trade count mismatch between DataFrame and journal
        - Trades present only in assets or only in journal
        - Unassigned trades
    """
    
    n_trades_df = len(df)
    n_trades_files = len(jr.trades)

    # Check for trade count mismatch
    if n_trades_df != n_trades_files:
        logging.warning(f"Trade count mismatch: {n_trades_df} in DataFrame vs {n_trades_files} in journal.")

    # Check for trades present only in assets
    asset_trades = set(df['trade_uid'])  # Assuming 'trade_uid' is the identifier in the DataFrame
    journal_trades = set(trade.uid for trade in jr.trades)  # Assuming 'uid' is the identifier in the Trade class

    only_in_assets = asset_trades - journal_trades
    only_in_journal = journal_trades - asset_trades

    if only_in_assets:
        logging.warning(f"Trades present only in assets: {only_in_assets}")
    
    if only_in_journal:
        logging.warning(f"Trades present only in journal: {only_in_journal}")

    # Check for unassigned trades
    unassigned_trades = [trade.uid for trade in jr.trades if not trade.has_tag('assigned')]
    if unassigned_trades:
        logging.warning(f"Unassigned trades found: {unassigned_trades}")

    # Use paths from TradeJournal
    assets_path = jr.ASSETS_PATH
    journal_root = jr.JOURNAL_ROOT

    # Example of using the paths
    logging.info(f"Assets path: {assets_path}")
    logging.info(f"Journal root: {journal_root}")

    # Get files for trades
    files = jr.get_files_for_trades(jr.ASSETS_PATH)
    
    # Check that each trade has at least a markdown file and some images
    for trade in jr.trades:
        trade_files = files.get(trade.uid, [])
        has_markdown = any(file.endswith('.md') for file in trade_files)
        has_images = any(file.endswith(('.png', '.jpg', '.jpeg', '.gif')) for file in trade_files)

        if not has_markdown:
            logging.warning(f"Trade {trade.uid} is missing a markdown file.")
        
        if not has_images:
            logging.warning(f"Trade {trade.uid} is missing image files.")

    
    
    
