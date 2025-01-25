import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
import seaborn as sns

import journal as jr

def perform_anova(df: pd.DataFrame, dependent_var: str, independent_var: str):
    """
    Perform ANOVA and return the summary.

    :param df: DataFrame containing the data.
    :param dependent_var: The dependent variable for ANOVA.
    :param independent_var: The independent categorical variable for ANOVA.
    :return: ANOVA summary.
    """
    formula = f'{dependent_var} ~ C({independent_var})'
    model = ols(formula, data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    return anova_table

def get_return_series(df, col='return_points'):
    """
    Get the return series from a trade dataframe.
    """
    s = df.set_index('entry_time')[col]
    s.sort_index(inplace=True)
    return s

def calculate_performance_metrics(df,):
    """
    Calculate key performance metrics for the trade dataframe.
    """
    
    # entry_time should be used in drawdown calculation
    return_series = get_return_series(df)
    
    metrics = {
        'Total Trades': len(df),
        'Total Return': df['return_points'].sum(),
        'Average Return': df['return_points'].mean(),
        'Max Return Drawdown': compute_max_drawdown(return_series),
    }
    
    if 'rr' in df.columns:
        metrics.update(
            {
                'Total Risk Reward Ratio': df['rr'].sum(),
                'Average Risk Reward Ratio': df['rr'].mean(),
                'Max Risk Reward Ratio': df['rr'].max(),
                'Min Risk Reward Ratio': df['rr'].min(),
            }
        )
    
    if 'outcome_win' in df.columns:
        metrics.update(
            {
                'Win Rate (%)': df['outcome_win'].mean(),
                'Average Win RR': df.loc[df['outcome_win'], 'rr'].mean(),
                'Max Win RR': df.loc[df['outcome_win'], 'rr'].max(),
                'Min Win RR': df.loc[df['outcome_win'], 'rr'].min(),
            }
        )
    if 'outcome_loss' in df.columns:
        metrics.update(
            {
                'Loss Rate (%)': df['outcome_loss'].mean(),
                'Average Loss RR': df.loc[df['outcome_loss'], 'rr'].mean(),
                'Max Loss RR': df.loc[df['outcome_loss'], 'rr'].min(),
                'Min Loss RR': df.loc[df['outcome_loss'], 'rr'].max(),
            }
        )
    
    if 'outcome_be' in df.columns:
        metrics.update(
            {
                'Breakeven Trades': df['outcome_be'].sum(),
                f'Breakeven Rate (%) (|rr|<{jr.Outcome.BE_THESHOLD})': df['outcome_be'].mean(),
            }
        )
    
    return pd.Series(metrics)

def compute_drawdown(series):
    """
    Compute the drawdown of a returns series.
    """
    cumulative = series.cumsum()
    peak = cumulative.expanding(min_periods=1).max()
    drawdown = peak - cumulative
    return cumulative, peak, drawdown


def compute_max_drawdown(series):
    """
    Compute the maximum drawdown of a returns series.
    """
    # check for datetime index
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError('Index of series must be a DatetimeIndex')
    
    # assert sorted index
    assert series.index.is_monotonic_increasing, 'Index must be sorted'

    cum, peak, dd = compute_drawdown(series)
    max_drawdown = dd.max()
    return max_drawdown

def plot_drawdown(series):
    """
    Plot the drawdown of a returns series with peak and returns.
    """
    cum, peak, drawdown = compute_drawdown(series)
    
    plt.figure(figsize=(10,6))
    drawdown.plot()
    peak.plot()
    cum.plot()
    plt.title('Drawdown of Trading Strategy')
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend(['Drawdown', 'Peak', 'Cumulative Return'])
    plt.show()

def plot_trade_distribution(df):
    """
    Plot the distribution of trade returns.
    """
    plt.figure(figsize=(10,6))
    sns.histplot(df['return_points'], bins=50, kde=True)
    plt.title('Distribution of Trade Returns')
    plt.xlabel('Return Points')
    plt.ylabel('Frequency')
    plt.legend(['Return Points'])
    plt.show()
