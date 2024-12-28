# Trade Journal Index
## Summary Statistics
Trade count: 4

Long trades: 4 (NaNs: 0)

Short trades: 0 (NaNs: 0)

Winrate: 25.00% (NaNs: 2)

Trade expectancy: -0.00 (NaNs: 2)

Total rows: 4

NaNs or skipped values: 28
## Tags Analysis
### Tags Statistics
| tag                      |   count |   unique_values |   missing_values | most_common                   |   most_common_freq |
|:-------------------------|--------:|----------------:|-----------------:|:------------------------------|-------------------:|
| entry_price              |       4 |               3 |                0 | 1.3                           |           0.25     |
| management_strategy      |       4 |               2 |                0 | no_management                 |           0.25     |
| confidence               |       1 |               1 |                3 | 4.0                           |           1        |
| SL_distance              |       4 |               3 |                0 | 0.5                           |           0.25     |
| type_1_m1                |       1 |               1 |                3 | True                          |           1        |
| potential_return         |       1 |               1 |                3 | 0.014999999999999902          |           1        |
| initial_risk_reward      |       4 |               3 |                0 | 9.99999999999963              |           0.25     |
| return                   |       2 |               2 |                2 | -0.014499999999999957         |           1        |
| potential_price          |       1 |               1 |                3 | 1.315                         |           1        |
| type_2_h1                |       1 |               1 |                3 | True                          |           1        |
| session                  |       4 |               2 |                0 | london                        |           0.5      |
| close_price              |       2 |               2 |                2 | 1.1855                        |           1        |
| tp_price                 |       4 |               3 |                0 | 1.33                          |           0.25     |
| entry_time               |       4 |               4 |                0 | 2024-12-25T10:00:00.000000000 |           1        |
| initial_return           |       4 |               2 |                0 | 0.010000000000000009          |           0.5      |
| TP_distance              |       4 |               2 |                0 | 0.010000000000000009          |           0.5      |
| potential_risk_reward    |       1 |               1 |                3 | 4.999999999999778             |           1        |
| sl_price                 |       4 |               3 |                0 | 1.297                         |           0.25     |
| outcome                  |       2 |               2 |                2 | loss                          |           1        |
| type_3_m15               |       1 |               1 |                3 | True                          |           1        |
| side                     |       4 |               1 |                0 | long                          |           0.25     |
| htf_poi_ltf_confirmation |       3 |               2 |                1 | False                         |           0.333333 |
| risk_reward_ratio        |       4 |               3 |                0 | 9.99999999999963              |           0.25     |
### Tags Distribution
|   entry_price |   confidence |   SL_distance |   potential_return |   initial_risk_reward |     return |   potential_price |   close_price |   tp_price | entry_time                    |   initial_return |   TP_distance |   potential_risk_reward |   sl_price |   risk_reward_ratio |
|--------------:|-------------:|--------------:|-------------------:|----------------------:|-----------:|------------------:|--------------:|-----------:|:------------------------------|-----------------:|--------------:|------------------------:|-----------:|--------------------:|
|     4         |            1 |      4        |              1     |              4        |  2         |             1     |     2         |   4        | 4                             |         4        |      4        |                       1 |  4         |            4        |
|     1.225     |            4 |      0.255    |              0.015 |              5.66667  | -0.00475   |             1.315 |     1.24525   |   1.245    | 2024-12-27 16:38:42.702448640 |         0.02     |      0.02     |                       5 |  1.2185    |            5.66667  |
|     1.1       |            4 |      0.005    |              0.015 |              0.666667 | -0.0145    |             1.315 |     1.1855    |   1.11     | 2024-12-25 10:00:00           |         0.01     |      0.01     |                       5 |  1.095     |            0.666667 |
|     1.175     |            4 |      0.0125   |              0.015 |              1.66667  | -0.009625  |             1.315 |     1.21537   |   1.185    | 2024-12-26 22:00:00.750000128 |         0.01     |      0.01     |                       5 |  1.1625    |            1.66667  |
|     1.25      |            4 |      0.2575   |              0.015 |              6        | -0.00475   |             1.315 |     1.24525   |   1.27     | 2024-12-28 04:38:42.952443136 |         0.02     |      0.02     |                       5 |  1.241     |            6        |
|     1.3       |            4 |      0.5      |              0.015 |             10        |  0.000125  |             1.315 |     1.27513   |   1.33     | 2024-12-28 23:17:24.904891648 |         0.03     |      0.03     |                       5 |  1.297     |           10        |
|     1.3       |            4 |      0.5      |              0.015 |             10        |  0.005     |             1.315 |     1.305     |   1.33     | 2024-12-28 23:17:24.904909    |         0.03     |      0.03     |                       5 |  1.297     |           10        |
|     0.0957427 |          nan |      0.282931 |            nan     |              5.03322  |  0.0137886 |           nan     |     0.0844993 |   0.106301 | nan                           |         0.011547 |      0.011547 |                     nan |  0.0978076 |            5.03322  |
## Trades
![Trade Outcomes](trade_outcomes.png)
This plot shows the distribution of trade outcomes (win/loss).
![Return Distribution](return_distribution.png)
This plot shows the distribution of returns for the trades. The histogram provides a visual representation of the frequency of different return values.
## DataFrame
|   trade_uid |   entry_price | management_strategy   |   confidence |   SL_distance | type_1_m1   |   potential_return |   initial_risk_reward |   return |   potential_price | type_2_h1   | session   |   close_price |   tp_price | entry_time                 |   initial_return |   TP_distance |   potential_risk_reward |   sl_price | outcome   | type_3_m15   | side   | htf_poi_ltf_confirmation   |   risk_reward_ratio |
|------------:|--------------:|:----------------------|-------------:|--------------:|:------------|-------------------:|----------------------:|---------:|------------------:|:------------|:----------|--------------:|-----------:|:---------------------------|-----------------:|--------------:|------------------------:|-----------:|:----------|:-------------|:-------|:---------------------------|--------------------:|
|           1 |           1.1 | no_management         |          nan |         0.005 | True        |            nan     |              2        | nan      |           nan     |             | tokyo     |      nan      |       1.11 | 2024-12-28 23:17:24.904886 |             0.01 |          0.01 |                     nan |      1.095 |           | True         | long   |                            |            2        |
|           2 |           1.2 | no_management         |          nan |         0.015 |             |            nan     |              0.666667 |  -0.0145 |           nan     | True        | tokyo     |        1.1855 |       1.21 | 2024-12-28 23:17:24.904909 |             0.01 |          0.01 |                     nan |      1.185 | loss      |              | long   | True                       |            0.666667 |
|           3 |           1.3 | no_management         |          nan |         0.5   |             |            nan     |             10        | nan      |           nan     |             | london    |      nan      |       1.33 | 2024-12-27 10:00:01        |             0.03 |          0.03 |                     nan |      1.297 |           |              | long   | False                      |           10        |
|           4 |           1.3 | strategy_2            |            4 |         0.5   |             |              0.015 |             10        |   0.005  |             1.315 |             | london    |        1.305  |       1.33 | 2024-12-25 10:00:00        |             0.03 |          0.03 |                       5 |      1.297 | win       |              | long   | False                      |           10        |
- [Trade 1](trade_1.md)
- [Trade 2](trade_2.md)
- [Trade 3](trade_3.md)
- [Trade 4](trade_4.md)