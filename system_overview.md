# System Overview

## Introduction
The Trading Journal System is designed to help traders manage and analyze their trades efficiently. It provides functionalities to add, update, list, and show trade details, along with calculating various metrics such as risk, planned risk-reward ratio (RR), actual RR, theoretical RR, and monetary outcome.

## Components

### 1. Trade Class
- Represents a trade with attributes like identifier, entry timestamp, symbol, lots, risk, account, balance, tags, planned RR, actual RR, theoretical RR, outcome.
- Methods:
  - `__repr__`: Returns a string representation of the trade.
  - `to_yaml`: Converts the trade object to YAML format.

### 2. TradeBuilder Class
- A builder pattern class to create and configure Trade objects.
- Methods:
  - Setters for various trade attributes (identifier, symbol, lots, risk, account, balance, tags, planned RR, actual RR, theoretical RR, outcome).
  - Calculation methods for risk, planned RR, actual RR, theoretical RR, and outcome.
  - `build`: Constructs and returns a Trade object.

### 3. Setup Class
- Represents a trade setup with attributes like identifier, entry style, tags, and market conditions.
- Methods:
  - `__repr__`: Returns a string representation of the setup.
  - `to_yaml`: Converts the setup object to YAML format.

### 4. Execution Class
- Represents an execution of a trade setup with attributes like identifier, setup identifier, account, risk percentage, entry price, stop loss (SL) pips, take profit (TP) pips, actual execution details, and tags.
- Methods:
  - `__repr__`: Returns a string representation of the execution.
  - `to_yaml`: Converts the execution object to YAML format.

### 5. CLI Commands
- `add_full`: Adds a new trade with full specification.
- `add_builder`: Adds a new trade using the builder pattern with optional calculations.
- `list`: Lists all trades with an option to show full details.
- `show`: Shows details of a specific trade by identifier.
- `update_trade`: Updates an existing trade with calculated metrics.
- `add_setup`: Adds a new trade setup.
- `add_execution`: Adds a new execution for a trade setup.

### 6. Utility Functions
- `ensure_trades_dir`: Ensures the trades directory exists.
- `save_trade`: Saves a trade object to a YAML file.
- `load_trade`: Loads a trade object from a YAML file.
- `get_trade_files`: Retrieves a list of trade files.
- `trade_constructor`: Custom constructor for loading Trade objects from YAML.
- `save_setup`: Saves a setup object to a YAML file.
- `load_setup`: Loads a setup object from a YAML file.
- `get_setup_files`: Retrieves a list of setup files.
- `setup_constructor`: Custom constructor for loading Setup objects from YAML.
- `save_execution`: Saves an execution object to a YAML file.
- `load_execution`: Loads an execution object from a YAML file.
- `get_execution_files`: Retrieves a list of execution files.
- `execution_constructor`: Custom constructor for loading Execution objects from YAML.

### 7. Configuration
- Uses environment variables for configuration (e.g., `JOURNAL_ROOT`).
- Logging configuration to handle different verbosity levels.

## Usage
- Install the package and set the root journal folder.
- Use the CLI commands to manage trades, setups, and executions.

## Future Enhancements
- Add more detailed trade analysis and reporting features.
- Integrate with external trading platforms for automated trade logging.
- Enhance the user interface for better usability.
- Analyze and visualize all trade tags in a large dataframe or similar to perform analysis of good combinations and statistics.