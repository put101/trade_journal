import yaml
from pathlib import Path
from tradecli import Trade, get_trade_files, load_trade

def analyze_trades_by_tag(tag):
    trades = []
    for file in get_trade_files():
        trade = load_trade(file)
        if tag in trade.tags:
            trades.append(trade)
    return trades

def calculate_average_outcome(trades):
    total_outcome = sum(trade.outcome for trade in trades if trade.outcome is not None)
    return total_outcome / len(trades) if trades else 0

def calculate_average_rr(trades, rr_type='planned'):
    rr_values = [getattr(trade, f'{rr_type}_rr') for trade in trades if getattr(trade, f'{rr_type}_rr') is not None]
    return sum(rr_values) / len(rr_values) if rr_values else 0

# Example usage
if __name__ == '__main__':
    tag = 'example_tag'
    trades_with_tag = analyze_trades_by_tag(tag)
    avg_outcome = calculate_average_outcome(trades_with_tag)
    avg_planned_rr = calculate_average_rr(trades_with_tag, 'planned')
    avg_actual_rr = calculate_average_rr(trades_with_tag, 'actual')
    avg_theoretical_rr = calculate_average_rr(trades_with_tag, 'theoretical')

    print(f"Average outcome for trades with tag '{tag}': {avg_outcome}")
    print(f"Average planned RR for trades with tag '{tag}': {avg_planned_rr}")
    print(f"Average actual RR for trades with tag '{tag}': {avg_actual_rr}")
    print(f"Average theoretical RR for trades with tag '{tag}': {avg_theoretical_rr}")
