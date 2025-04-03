# src/tradecli.py

from dataclasses import dataclass, field
from joblib import Parallel, delayed
from typing import List, Dict, Union, Optional, override
import pandas as pd
from datetime import datetime
import os
import pathlib
import copy
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import itertools
import logging
from tqdm import tqdm
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression
import re
import json
import numpy as np
import pprint
from typing import Optional, List, Dict, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import re
import pprint
import features



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Config:
    """Configuration for data analysis."""

    def __init__(
        self,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        force_values: Optional[Dict[str, any]] = None
    ):
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.force_values = force_values or {}


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

    def pp_tags_dict(self):
        # pp the tags dict
        pprint.pprint(self.get_tags_dict())
    
    
    def print_trade_info(self):
        print(f"Trade UID: {self.uid}")
        print(f"Tags: {self.get_tags_dict()}")

    
    def get_tag(self, key: str) -> Union[bool, float]:
        return next((tag.value for tag in self.tags if tag.key == key), None)
    
    
    
    def get_tags(self) -> List[Tag]:
        return self.tags




@dataclass
class TradeJournal:
    trades: List[Trade] = field(default_factory=list)
    # path to the assets folder inside the project
    ENV_JOURNAL_ROOT = os.environ.get('JOURNAL_ROOT')
    CWD_JOURNAL_ROOT = os.getcwd()
    if ENV_JOURNAL_ROOT is None:
        raise ValueError("JOURNAL_ROOT environment variable not set.")
    
    JOURNAL_ROOT = pathlib.Path(ENV_JOURNAL_ROOT)
    
    ASSETS_PATH = JOURNAL_ROOT / 'assets'
    EXPORT_PATH = JOURNAL_ROOT / 'export'
    logging.info(f"Journal root: {JOURNAL_ROOT}")
    logging.info(f"CMD Journal root: {CWD_JOURNAL_ROOT}")
    logging.info(f"Assets root: {ASSETS_PATH}")
    logging.info(f"Export root: {EXPORT_PATH}")
    
    
    @override
    def get_all_categorical_tags(self) -> List[str]:
        for trade in self.trades:
            for tag in trade.tags:
                if tag.key in features.get_all_categorical_tags():
                    yield tag.key
        

    @override
    def get_all_ignored_tags(self) -> List[str]:
        raise NotImplementedError(
            "This method should be implemented in a subclass.")

    def add_trade(self, trade: Trade):
        logging.info(f"Adding trade with UID: {trade.uid}")
        self.trades.append(trade)

    def to_dataframe(self, config: Optional[Config] = None) -> pd.DataFrame:
        data = []
        all_tags = set(tag.key for trade in self.trades for tag in trade.tags)
        for trade in self.trades:
            row = {'trade_uid': trade.uid}
            for tag in all_tags:
                tag_value = next(
                    (t.value for t in trade.tags if t.key == tag), None)
                # Apply forced values from config
                if config and tag in config.force_values:
                    row[tag] = config.force_values[tag]
                else:
                    row[tag] = tag_value
            data.append(row)
        df = pd.DataFrame(data)

        # Apply inclusion/exclusion patterns
        if config:
            if config.include_patterns:
                df = df.filter(regex='|'.join(config.include_patterns))
            if config.exclude_patterns:
                exclude_regex = '|'.join(config.exclude_patterns)
                df = df.drop(columns=[col for col in df.columns if re.search(
                    exclude_regex, col)], errors='ignore')

        # Detect and convert boolean columns
        for col in df.columns:
            unique_values = df[col].dropna().unique()
            if set(unique_values).issubset({True, False}):
                logging.debug(f"Converting column {col} to boolean")
                #df[col] = df[col].astype(bool)  
                df[col] = df[col].astype('boolean')
            
      # Convert categorical columns
        categorical_tags = self.get_all_categorical_tags()
        for col in categorical_tags:
            if col in df.columns:
                df[col] = df[col].astype('category')

        # Pivot categorical columns
        df = self.pivot_categorical_columns(df, categorical_tags)

        return df

    def pivot_categorical_columns(self, df: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
        for col in categorical_columns:
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df, dummies], axis=1)
        return df

    def get_simple_statistics(self) -> str:
        logging.info("Calculating simple statistics")
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
                f"Trade expectancy: {
                    trade_expectancy:.2f} (NaNs: {n_return_nans})\n\n"
                f"Total rows: {total_rows}\n\n"
                f"NaNs or skipped values: {nans}")

    def get_tags_statistics(self) -> pd.DataFrame:
        logging.info("Calculating tags statistics")
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

    def analyze_tag_relevance(self) -> pd.DataFrame:
        logging.info("Analyzing tag relevance")
        df = self.to_dataframe()
        if df.empty:
            return pd.DataFrame()

        tags = [col for col in df.columns if col not in [
            'trade_uid', 'return', 'outcome']]
        analysis_data = []

        for tag in tags:
            tag_df = df.dropna(subset=[tag])
            if tag_df.empty:
                continue
            winrate = tag_df[tag_df['outcome'] ==
                             'win'].shape[0] / tag_df.shape[0] * 100
            expectancy = tag_df['return'].mean()
            skipped = df.shape[0] - tag_df.shape[0]
            nans = df[tag].isnull().sum()
            analysis_data.append({
                'tag': tag,
                'count': tag_df.shape[0],
                'winrate': winrate,
                'expectancy': expectancy,
                'skipped': skipped,
                'nans': nans
            })

        return pd.DataFrame(analysis_data)

    def plot_statistics(self, output_dir: str):
        logging.info("Plotting statistics")
        df = self.to_dataframe()
        if df.empty:
            return

        plt.style.use('dark_background')
        sns.set_palette("bright")

        total_rows = df.shape[0]
        skipped_rows_outcome = df['outcome'].isnull().sum()
        skipped_rows_return = df['return'].isnull().sum()

        plt.figure(figsize=(10, 6))
        sns.countplot(x='outcome', data=df)
        plt.title(f'Trade Outcomes (Total rows: {
                  total_rows}, Skipped rows: {skipped_rows_outcome})')
        plt.xlabel('Outcome')
        plt.ylabel('Count')
        plt.savefig(os.path.join(output_dir, 'trade_outcomes.png'))
        plt.close()

        plt.figure(figsize=(10, 6))
        sns.histplot(df['return'].dropna(), kde=True)
        plt.title(f'Return Distribution (Total rows: {
                  total_rows}, Skipped rows: {skipped_rows_return})')
        plt.xlabel('Return')
        plt.ylabel('Frequency')
        plt.savefig(os.path.join(output_dir, 'return_distribution.png'))
        plt.close()

    def write_index_markdown(self, output_dir: str, config: Optional[Config] = None):
        logging.info("Writing index markdown")
        index_path = os.path.join(output_dir, "index.md")
        stats = self.get_simple_statistics()
        df = self.to_dataframe()
        tag_relevance_df = self.analyze_tag_relevance()
        logging.info("Finding best single tags and subsets")
        best_tags = self.find_best_tags(top_n=5)
        logging.info("Finding best tag subsets")
        best_subsets = self.find_best_tag_subsets_FULL_PARALLEL(
            top_n=5, max_subset_size=6)

        # Get selected features from RFE
        selected_features = self.select_good_features()

        ignored_tags = self.get_all_ignored_tags()

        lines = [
            "# Trade Journal Index",
            "## Summary Statistics",
            stats,
            "## Tags Analysis",
            "### Tags Statistics",
            self.get_tags_statistics().to_markdown(index=False),
            "### Tags Distribution",
            self.to_dataframe(config).describe().to_markdown(index=False),
            "### Tags Relevance",
            tag_relevance_df.to_markdown(index=False),
            "### Best Single Tags",
            best_tags.to_markdown(index=False),
            "### Best Tag Subsets",
            best_subsets.to_markdown(index=False),
            "### Selected Features using RFE",
            ", ".join(selected_features),
            "## Ignored Tags",
            ", ".join(ignored_tags),
            "## Trades",
            "![Trade Outcomes](trade_outcomes.png)",
            "This plot shows the distribution of trade outcomes (win/loss).",
            "![Return Distribution](return_distribution.png)",
            "This plot shows the distribution of returns for the trades. The histogram provides a visual representation of the frequency of different return values.",
            "## DataFrame",
            df.to_markdown(index=False),
            "## Detailed Queries",  # Renamed from "Specific Queries"
        ]

        # Generate links to specific query markdown files
        if config:
            for idx, query in enumerate(config.include_patterns, start=1):
                lines.append(f"- [Query {idx}: {query}](query_{idx}.md)")

        for trade in self.trades:
            lines.append(f"- [Trade {trade.uid}](trade_{trade.uid}.md)")
        with open(index_path, 'w') as index_file:
            index_file.write("\n".join(lines))

    def to_markdown(self, output_dir: str, config: Optional[Config] = None, df: Optional[pd.DataFrame] = None):
        logging.info("Converting trades to markdown")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        def get_files_for_trades(p: pathlib.Path) -> Dict[str, List[str]]:
            """Files are structured arbitrarly by the user. 
            Assets need to be below the ASSETS_PATH folder in any strucutre and files are attributed in named-sorted order
            to the trade ID if found somewhere in a file's path. This enables the user to structure and name the assets as they like. 
            """
            import glob
            files = {}

            for trade in self.trades:
                trade_id = trade.uid
                files[trade_id] = []
                for asset in glob.glob(os.path.join(p, '**', '*'), recursive=True):
                    if trade_id in asset:
                        files[trade_id].append(asset)
                # sort the files by name
                files[trade_id].sort()

            logging.info("Files for trades found")
            logging.info(f"Files Found #: {len(files)}, Total Trades #: {len(self.trades)}"
                         + f"max files for trade: {max([len(files[trade.uid]) for trade in self.trades])}"
                         + f"min files for trade: {min([len(files[trade.uid]) for trade in self.trades])}"
                         + f"avg files for trade: {sum([len(files[trade.uid]) for trade in self.trades]) / len(self.trades)}")
            # do similar descriptive statistics using pandas
            # pd.DataFrame([len(files[trade.uid]) for trade in self.trades]).describe()
            file_stats = pd.DataFrame([len(files[trade.uid])
                                      for trade in self.trades])
            logging.info(f"Descriptive Statistics: {file_stats.describe()}")

            return files

        assets = get_files_for_trades(self.ASSETS_PATH)
        logging.debug(f"Assets: {assets}")

        if df is None:
            df = self.to_dataframe(config)

        for trade in self.trades:
            md_path = os.path.join(output_dir, f"trade_{trade.uid}.md")
            full_row = df[df['trade_uid'] == trade.uid].to_dict(orient='records')
            pretty_row = json.dumps(full_row, indent=4, default=str)  # Pretty print JSON
            md_content = f"# Trade Summary\n\n"
            md_content += f"**Trade UID:** {trade.uid} \n\n"
            md_content += f"**Tags:**\n"
            md_content += "```\n"
            for tag in trade.tags:
                md_content += f"{tag.key}: {tag.value}\n"
            md_content += "```\n\n"

            md_content += f"## Full DataRow\n\n"
            md_content += "```\n"
            md_content += f"{pretty_row}\n"
            md_content += "```\n\n"

            md_content += f"## Assets\n\n"
            if trade.uid in assets:
                for asset in assets[trade.uid]:
                    md_content += f"![Asset]({asset})\n\n"

            md_content += f"## Trade Plot Explanation\n\n"

            md_content += "\n[Back to Index](index.md)\n"

            with open(md_path, 'w') as md_file:
                md_file.write(md_content)

        self.write_index_markdown(output_dir, config)
        self.plot_statistics(output_dir)

    def find_best_tags(self, top_n: int = 5) -> pd.DataFrame:
        logging.info("Finding best single tags")
        df = self.to_dataframe()
        if df.empty:
            return pd.DataFrame()

        ignored_tags = self.get_all_ignored_tags()
        tags = [col for col in df.columns if col not in [
            'trade_uid', 'return', 'outcome'] and col not in ignored_tags]
        results = []

        for tag in tags:
            tag_df = df.dropna(subset=[tag])
            if tag_df.empty:
                continue

            winrate = tag_df[tag_df['outcome'] ==
                             'win'].shape[0] / tag_df.shape[0] * 100
            expectancy = tag_df['return'].mean()
            if pd.isna(expectancy):
                logging.warning(f"Expectancy is NaN for tag {tag}")
                continue

            results.append({
                'tag': tag,
                'count': tag_df.shape[0],
                'winrate': winrate,
                'expectancy': expectancy
            })

        results_df = pd.DataFrame(results)
        return results_df.sort_values(by='expectancy', ascending=False).head(top_n)

    @staticmethod
    def calculate_subset(subset, df):
        subset_df = df.dropna(subset=subset)
        if subset_df.empty:
            return None

        winrate = subset_df[subset_df['outcome'] ==
                            'win'].shape[0] / subset_df.shape[0] * 100
        expectancy = subset_df['return'].mean()

        return {
            'tags': subset,
            'count': subset_df.shape[0],
            'winrate': winrate,
            'expectancy': expectancy
        }

    def select_good_features(self, top_n: int = 10) -> List[str]:
        """
        Select top_n features using Recursive Feature Elimination with Logistic Regression,
        excluding outcome-related one-hot encoded columns.
        """
        logging.info(f"Selecting top {top_n} features using RFE")
        df = self.to_dataframe()
        if df.empty:
            logging.warning("DataFrame is empty. No features to select.")
            return []

        # Drop columns with all NaNs
        df = df.dropna(axis=1, how='all')

        # Assume 'outcome' is the target variable
        if 'outcome' not in df.columns:
            logging.error("'outcome' column not found in DataFrame.")
            return []

        # Drop rows with NaN in 'outcome'
        df_old = df
        df = df.dropna(subset=['outcome'])
        logging.info(f"Dropped {
                     df_old.shape[0] - df.shape[0]} rows with NaN in 'outcome' y variable")

        y = df['outcome'].apply(
            lambda x: 1 if x == 'win' else 0)  # Binary encoding

        cols = set(df.columns) - \
            set(['trade_uid', 'outcome'] + self.get_all_ignored_tags())
        logging.info(f"X features # {len(cols)}: {cols}")
        X = df[list(cols)]

        # Convert datetime columns to numerical values
        for col in X.select_dtypes(include=['datetime64']).columns:
            # Convert to seconds since epoch
            X[col] = X[col].astype('int64') // 10**9

        # Handle categorical variables by one-hot encoding, excluding 'confidence_*'
        categorical_cols = [
            col for col in X.select_dtypes(include=['category', 'object']).columns
            if not col.startswith('confidence_')
        ]
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

        # Fill NaN values with a default or appropriate value
        X = X.fillna(0)
        logging.debug("Filled NaN values in feature matrix with 0")

        # Exclude outcome-related one-hot encoded columns
        X = X.drop(columns=[col for col in X.columns if col.startswith(
            'outcome_')], errors='ignore')

        # Remove any remaining 'confidence_*' related features just in case
        confidence_cols = [
            col for col in X.columns if col.startswith('confidence_')]
        if confidence_cols:
            X = X.drop(columns=confidence_cols, errors='ignore')
            logging.info(f"Dropped duplicate confidence columns: {
                         confidence_cols}")

        model = LogisticRegression(max_iter=1000)
        rfe = RFE(model, n_features_to_select=top_n)
        try:
            rfe.fit(X, y)
            selected_features = X.columns[rfe.support_].tolist()
            logging.info(f"Selected features # {
                         len(selected_features)}: {selected_features}")

            # Log feature rankings
            feature_ranking = sorted(
                zip(X.columns, rfe.ranking_), key=lambda x: x[1])
            logging.info("RFE Feature Rankings:")
            for feature, rank in feature_ranking:
                logging.info(f"{feature}: Rank {rank}")

            return selected_features
        except Exception as e:
            logging.error(f"Error during feature selection: {e}")
            return []

    def find_best_tag_subsets_FULL_PARALLEL(self, top_n: int = 5, max_subset_size: int = 4) -> pd.DataFrame:
        logging.info("Finding best tag subsets")
        df = self.to_dataframe()
        if df.empty:
            return pd.DataFrame()

        ignored_tags = self.get_all_ignored_tags()
        # Select good features first
        selected_features = self.select_good_features(top_n=10)
        if not selected_features:
            logging.error(
                "No features selected. Aborting tag subset calculation.")
            raise ValueError("No features selected.")
        # Filter tags based on selected features
        tags = [col for col in selected_features if col not in [
            'trade_uid', 'return', 'outcome'] and col not in ignored_tags]
        results = []

        logging.info(f"Calculating tag subsets for selected tags: {tags}")

        import time
        for i in range(1, min(len(tags), max_subset_size) + 1):
            num_combinations = len(list(itertools.combinations(tags, i)))
            logging.info(f"Number of combinations for subset size {
                         i}: {num_combinations}")

            subset_combinations = list(itertools.combinations(tags, i))

            start_time = time.time()
            logging.info(f"Starting parallel subset calculations for subset size {
                         i} with Joblib")
            subset_results = Parallel(n_jobs=-1)(
                delayed(TradeJournal.calculate_subset)(subset, df) for subset in subset_combinations
            )
            end_time = time.time()
            duration = end_time - start_time
            logging.info(f"Parallel subset calculation for subset size {
                         i} completed in {duration:.2f} seconds")

            results.extend([result for result in subset_results if result and not pd.isna(result['expectancy'])])

        results_df = pd.DataFrame(results)

        return results_df.sort_values(by='expectancy', ascending=False).head(top_n)

    def export_dataframe_for_r(self, df: pd.DataFrame, export_dir: str):
        """
        Export the DataFrame to an Excel file and save the list of relevant columns to a JSON file for R analysis.
        """
        os.makedirs(export_dir, exist_ok=True)
        excel_path = os.path.join(export_dir, 'trade_data.xlsx')
        cols_path = os.path.join(export_dir, 'relevant_columns.json')
        
        # Save DataFrame to Excel
        df.to_excel(excel_path, index=False)
        logging.info(f"Exported DataFrame to {excel_path}")
        
        # Define relevant columns (example: excluding 'trade_uid')
        relevant_columns = [col for col in df.columns if col != 'trade_uid']
        
        # Save relevant columns to JSON
        with open(cols_path, 'w') as f:
            json.dump(relevant_columns, f, indent=4)
        logging.info(f"Exported relevant columns to {cols_path}")

        # Save DataFrame to CSV
        csv_path = os.path.join(export_dir, 'trade_data.csv')
        df.to_csv(csv_path, index=False)
        logging.info(f"Exported DataFrame to {csv_path}")
        
        # Save DataFrame to Feather
        feather_path = os.path.join(export_dir, 'trade_data.feather')
        df.to_feather(feather_path)
        logging.info(f"Exported DataFrame to {feather_path}")
        
        # Save DataFrame to Parquet
        parquet_path = os.path.join(export_dir, 'trade_data.parquet')
        df.to_parquet(parquet_path)
        logging.info(f"Exported DataFrame to {parquet_path}")
       
        # Save DataFrame to json
        json_path = os.path.join(export_dir, 'trade_data.json')
        df.to_json(json_path)
        logging.info(f"Exported DataFrame to {json_path}")
        



class ReportOptunaConfig:
    """Configuration for Optuna hyperparameter optimization."""

    def __init__(
        self,
        n_trials: int = 100,
        n_jobs: int = 1,
        timeout: Optional[int] = None,
        study_name: str = 'default',
        direction: str = 'maximize'
    ):
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.timeout = timeout
        self.study_name = study_name
        self.direction = direction
    
from itertools import combinations, product



def report_best_performing_tags_value(df, y_col:str, feat_cols:Optional[list]=None, score_mode='mean', method='brute_force', config:any=None):
    """_summary_

    Args:
        df (_type_): _description_
        feat_cols (_type_): _description_
        y_col (_type_): _description_
        
    Prints the best subset of tags and combinations for the given dataframe features and target column output.
    It should find the highest scoring tags and their values for the given target column.
    It does not use a model but rather try to find the best combination of tags 
    """

    best_subset = None
    best_score = -1
    best_combination = None

    if feat_cols is None:
        feat_cols = df.columns.tolist()
        feat_cols.remove(y_col)
        
    unique_values_dict = {col: df[col].unique().tolist() for col in feat_cols}
    logging.info(f"Unique values for each feature:\n{unique_values_dict}")

    if method == 'brute_force':
        for i in range(1, len(feat_cols) + 1):
            for subset in itertools.combinations(feat_cols, i):
                for combination in itertools.product(*[df[col].unique() for col in subset]):
                    mask = df[list(subset)].apply(lambda x: x == combination, axis=1).all(axis=1)
                    if score_mode == 'mean':
                        try:
                            score = df[mask][y_col].mean()
                            if pd.isna(score):
                                logging.warning(f"Score is NaN for subset {subset} with combination {combination}")
                                continue
                        except Exception as e:
                            logging.error(f"Error calculating mean for {y_col}: {e}")
                            score = None
                    
                    if score > best_score:
                        best_score = score
                        best_subset = subset
                        best_combination = combination
                        print(f"Best subset: {best_subset}")
                        print(f"Best combination: {best_combination}")
                        print(f"Best score: {best_score}")
        
        # end i
        
        print(f"Best subset: {best_subset}")
        print(f"Best combination: {best_combination}")
        print(f"Best score: {best_score}")
    
    if method == 'optuna':
        assert config is not None, "Optuna configuration is required for optuna method"
        assert isinstance(config, ReportOptunaConfig), f"Optuna config {type(config)} wrong type"
        import optuna
        from optuna.samplers import TPESampler
        from optuna.trial import TrialState
        from optuna.study import StudyDirection
        from optuna.study import create_study
        
        """Optimize which tags and their values are best for the given target column
        Not using all tags is likely the best
        """
        
        all_tag_unique_values = {col: df[col].unique().tolist() for col in feat_cols}
        
        def objective(trial: optuna.Trial):
            selected_tags = []
            combination_values = {}
            for tag in feat_cols:
                include = trial.suggest_categorical(f'include_{tag}', [True, False])
                if include:
                    value = trial.suggest_categorical(f'value_{tag}', all_tag_unique_values[tag])
                    selected_tags.append(tag)
                    combination_values[tag] = value
            
            if selected_tags:
                mask = pd.Series([True] * len(df), index=df.index)
                for tag, value in combination_values.items():
                    mask &= df[tag] == value
            else:
                return -np.inf

            if score_mode == 'mean':
                try:
                    score = df.loc[mask][y_col].mean()
                    if pd.isna(score):
                        logging.warning(f"Score is NaN for trial with tags {combination_values}")
                        return -np.inf  # Assign a very low score to failed trials
                    trial.set_user_attr('remaining_rows', df.loc[mask].to_dict())
                except Exception as e:
                    logging.error(f"Error calculating mean for {y_col}: {e}")
                    return -np.inf

            return score

        study = create_study(
            direction=StudyDirection.MAXIMIZE if config.direction == 'maximize' else StudyDirection.MINIMIZE,
            study_name=config.study_name,
            sampler=TPESampler()
        )
        study.optimize(
            objective,
            n_trials=config.n_trials,
            n_jobs=config.n_jobs,
            timeout=config.timeout,
            show_progress_bar=True
        )
        best_params = study.best_params
        best_score = study.best_value
        print(f"Best parameters: {best_params}")
        print(f"Best score: {best_score}")
        return study, best_params, best_score
