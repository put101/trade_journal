import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import numpy as np
from matplotlib.patches import Rectangle
import logging

import journal as jr

from functools import partial


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
    
    time_col = 'entry_time'
    
    # Check for missing timestamps
    if df['entry_time'].isnull().any():
        logging.warn(f"Some '{time_col}' values are missing. Rows with missing timestamps will be dropped.")
    
    # Drop rows with missing timestamps
    df = df.dropna(subset=[time_col])
    
    s = df.set_index(time_col)[col]
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
    
    drawdown = -drawdown
    
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


def plot_profit_calendar_matplotlib(df: pd.DataFrame, col='return', ts_col='entry_time', month=None, year=None):
    """
    Plot an actual calendar visualization with daily profit data.
    
    Args:
        df (pd.DataFrame): A trade journal dataframe.
        col (str): Column name containing the profit/return values.
        ts_col (str, optional): Column name for timestamp if not using index.
        month (int, optional): Specific month to plot (1-12). If None, uses the current month.
        year (int, optional): Specific year to plot. If None, uses the current year.
        
    Returns:
        matplotlib.figure: The figure object created.
    """
    df = df.copy()  # Make a copy to avoid modifying the original
    
    # Handle timestamp column if provided
    if ts_col is not None:
        if ts_col not in df.columns:
            raise ValueError(f'Column {ts_col} not found in dataframe')
        df.set_index(ts_col, inplace=True)
        df.sort_index(inplace=True)
    
    
    # Verify we have datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError('Index of dataframe must be a DatetimeIndex')
    
    # Check if column exists
    if col not in df.columns:
        raise ValueError(f'Column {col} not found in dataframe')
    
    # Get daily profits (sum by day)
    daily_profit = df[col].resample('D').sum()
    
    # Determine month and year to display
    if month is None or year is None:
        if not daily_profit.empty:
            # Use the month and year of the most recent data
            latest_date = daily_profit.index[-1]
            month = month or latest_date.month
            year = year or latest_date.year
        else:
            # If no data, use current month/year
            from datetime import datetime
            now = datetime.now()
            month = month or now.month
            year = year or now.year
    
    # Create a new figure with a reasonable size for a calendar
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Get month information
    month_name = calendar.month_name[month]
    num_days = calendar.monthrange(year, month)[1]
    first_day_weekday = calendar.weekday(year, month, 1)  # 0 is Monday in Python's calendar
    
    # Create day labels (Monday through Sunday)
    day_names = list(calendar.day_name)
    # Reorder to start with Monday if using Monday as first day of week
    day_names = day_names[0:] + day_names[:0]  # Adjust this if needed for different first day of week
    
    # Set up the grid
    num_rows = (num_days + first_day_weekday - 0 + 6) // 7
    ax.set_xlim(0, 7)
    ax.set_ylim(0, num_rows)
    
    # Remove axes
    ax.axis('off')
    
    # Add title
    ax.set_title(f"{month_name} {year}", fontsize=12, fontweight='bold')
    
    # add more space between everything
    
    
    # Add day names
    for i, day in enumerate(day_names):
        ax.text(i + 0.5, num_rows + 0.25, day, ha='center', fontsize=12)
    
    # Generate date strings for the month
    dates = [f"{year}-{month:02d}-{day:02d}" for day in range(1, num_days + 1)]
    date_profits = {}
    
    # Get profit values for each date in the month
    for date_str in dates:
        date = pd.Timestamp(date_str)
        if date in daily_profit.index:
            date_profits[date_str] = daily_profit.loc[date]
        else:
            date_profits[date_str] = 0
    
    # Define color scale
    max_abs_profit = max(abs(max(date_profits.values())), abs(min(date_profits.values()))) if date_profits else 1
    
    # Function to get color based on profit
    def get_color(profit, max_value=max_abs_profit):
        if profit == 0:
            return 'white'
        elif profit > 0:
            intensity = min(0.8, (profit / max_value) * 0.8) + 0.2
            return (0, intensity, 0)  # Green
        else:
            intensity = min(0.8, (abs(profit) / max_value) * 0.8) + 0.2
            return (intensity, 0, 0)  # Red
    
    # Plot each day as a cell in the calendar
    day = 1
    for row in range(num_rows):
        for col in range(7):
            # Skip cells before the first day of the month
            if row == 0 and col < first_day_weekday:
                continue
            
            # Stop after reaching the last day of the month
            if day > num_days:
                break
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            profit = date_profits.get(date_str, 0)
            
            # Create a rectangle for the day
            rect = Rectangle((col, num_rows - row - 1), 1, 1, 
                            linewidth=1, edgecolor='gray', facecolor=get_color(profit))
            ax.add_patch(rect)
            
            # Add day number
            ax.text(col + 0.05, num_rows - row - 0.25, f"{day}", fontsize=10, ha='left', va='top')
            
            # Add profit value
            if profit != 0:
                color = 'white' if abs(profit) > max_abs_profit * 0.3 else 'black'
                ax.text(col + 0.5, num_rows - row - 0.6, f"{profit:.2f}", 
                       fontsize=9, ha='center', va='center', color=color)
            
            day += 1
    
    # Add a color bar legend
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn, 
                               norm=plt.Normalize(vmin=-max_abs_profit, vmax=max_abs_profit))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', shrink=0.7)
    cbar.set_label('Daily Profit')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)  # Make room for title
    
    return fig

def plot_calendar_calplot(df:pd.DataFrame):
    """Use a more modern library for plotting

    Args:
        df (pd.DataFrame): _description_
    """
    
    # Use calplot for a more modern calendar plot
    import calplot
    
    COL_TIME = 'entry_time'
    COL_SERIES = 'return'
    
    df = df.copy()
    df[COL_TIME] = pd.to_datetime(df[COL_TIME])
    df.set_index(COL_TIME,inplace=True)
    df.sort_index(inplace=True)
    
    # Get daily returns
    daily_returns = df[COL_SERIES].resample('D').sum()
    
    # Use calplot to plot the calendar
    light_green_red_palette = sns.diverging_palette(150, 10, as_cmap=True)
    
    calplot.calplot(daily_returns, cmap=light_green_red_palette,
                    figsize=(40,10),
                    tight_layout=True,
                    colorbar=True, 
                    edgecolor='gray', 
                    textformat='{:.00f}', 
                    #textfiller='-',
                    dropzero=True,
                    dayticks=True,
                    )
    
    plt.show()
    
    
def plot_calendar_calendarplot(df:pd.DataFrame):
    from calendarplot import create_year_calendar
    from matplotlib.colors import ListedColormap
    
    COL_TIME = 'entry_time'
    COL_SERIES = 'return'
    YEAR = 2024
    
    
    df = df.copy()
    df[COL_TIME] = pd.to_datetime(df[COL_TIME])
    df.set_index(COL_TIME,inplace=True)
    df.sort_index(inplace=True)
    
    # Get daily returns
    SERIES = df[COL_SERIES].resample('D').sum()
    
    cmap = 'PiYG'    
    
    create_year_calendar(SERIES, YEAR, f'{YEAR} Heatmap', 'example_calendar.png', cmap=cmap, showcb=True)
    
def plot_column_distributions(df: pd.DataFrame, columns: list, figsize=(15, 5)):
    num_cols = len(columns)
    fig, axes = plt.subplots(1, num_cols, figsize=figsize)
    
    # Ensure axes is always a list
    if num_cols == 1:
        axes = [axes]
    
    for ax, col in zip(axes, columns):
        # Convert column to object type and fill NaN values with "None"
        data = df[col].astype(object).fillna("None")
        order = data.value_counts().index  # Order by frequency
        sns.countplot(x=data, ax=ax, order=order)
        
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.show()


def plot_feature_distributions(df: pd.DataFrame, features: list, cell_size=3):
    # Create a grid of subplots
    n_features = len(features)
    n_cols = 3  # You can adjust this number
    n_rows = (n_features + n_cols - 1) // n_cols


    size_per_cell = cell_size
    fs = (n_cols * size_per_cell, n_rows * size_per_cell)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=fs)

    # Flatten the axes array for easier indexing
    axes = axes.flatten()
    
    for i, feature in enumerate(features):
        sns.histplot(df[feature].astype(str), ax=axes[i])
        axes[i].set_title(feature)

    plt.tight_layout()
    plt.show()


def plot_hist_all_values_col(df: pd.DataFrame, col:str):
    df[col].value_counts(dropna=False).plot(kind='bar')
    plt.title(col)
    plt.show()
    print(df[col].value_counts(dropna=False))
    
def get_trades_col_nan(df: pd.DataFrame, col:str):
    """
    Get trade_uids for the NaN values of certain column
    """

    return df[df[col].isna()]['trade_uid']