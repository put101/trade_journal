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
| confidence               |       1 |               1 |                3 | 4.0                           |           1        |
| entry_price              |       4 |               3 |                0 | 1.3                           |           0.25     |
| initial_risk_reward      |       4 |               3 |                0 | 9.99999999999963              |           0.25     |
| type_3_m15               |       1 |               1 |                3 | True                          |           1        |
| potential_return         |       1 |               1 |                3 | 0.014999999999999902          |           1        |
| management_strategy      |       4 |               2 |                0 | no_management                 |           0.25     |
| potential_price          |       1 |               1 |                3 | 1.315                         |           1        |
| session                  |       4 |               2 |                0 | london                        |           0.5      |
| SL_distance              |       4 |               3 |                0 | 0.5                           |           0.25     |
| TP_distance              |       4 |               2 |                0 | 0.010000000000000009          |           0.5      |
| potential_risk_reward    |       1 |               1 |                3 | 4.999999999999778             |           1        |
| entry_time               |       4 |               4 |                0 | 2024-12-25T10:00:00.000000000 |           1        |
| risk_reward_ratio        |       4 |               3 |                0 | 9.99999999999963              |           0.25     |
| sl_price                 |       4 |               3 |                0 | 1.297                         |           0.25     |
| side                     |       4 |               1 |                0 | long                          |           0.25     |
| type_2_h1                |       1 |               1 |                3 | True                          |           1        |
| return                   |       2 |               2 |                2 | -0.014499999999999957         |           1        |
| outcome                  |       2 |               2 |                2 | loss                          |           1        |
| initial_return           |       4 |               2 |                0 | 0.010000000000000009          |           0.5      |
| type_1_m1                |       1 |               1 |                3 | True                          |           1        |
| tp_price                 |       4 |               3 |                0 | 1.33                          |           0.25     |
| htf_poi_ltf_confirmation |       3 |               2 |                1 | False                         |           0.333333 |
| close_price              |       2 |               2 |                2 | 1.1855                        |           1        |
### Tags Distribution
|   confidence |   entry_price |   initial_risk_reward |   potential_return |   potential_price |   SL_distance |   TP_distance |   potential_risk_reward | entry_time                    |   risk_reward_ratio |   sl_price |     return |   initial_return |   tp_price |   close_price |
|-------------:|--------------:|----------------------:|-------------------:|------------------:|--------------:|--------------:|------------------------:|:------------------------------|--------------------:|-----------:|-----------:|-----------------:|-----------:|--------------:|
|            1 |     4         |              4        |              1     |             1     |      4        |      4        |                       1 | 4                             |            4        |  4         |  2         |         4        |   4        |     2         |
|            4 |     1.225     |              5.66667  |              0.015 |             1.315 |      0.255    |      0.02     |                       5 | 2024-12-27 16:51:43.786096640 |            5.66667  |  1.2185    | -0.00475   |         0.02     |   1.245    |     1.24525   |
|            4 |     1.1       |              0.666667 |              0.015 |             1.315 |      0.005    |      0.01     |                       5 | 2024-12-25 10:00:00           |            0.666667 |  1.095     | -0.0145    |         0.01     |   1.11     |     1.1855    |
|            4 |     1.175     |              1.66667  |              0.015 |             1.315 |      0.0125   |      0.01     |                       5 | 2024-12-26 22:00:00.750000128 |            1.66667  |  1.1625    | -0.009625  |         0.01     |   1.185    |     1.21537   |
|            4 |     1.25      |              6        |              0.015 |             1.315 |      0.2575   |      0.02     |                       5 | 2024-12-28 04:51:44.036090368 |            6        |  1.241     | -0.00475   |         0.02     |   1.27     |     1.24525   |
|            4 |     1.3       |             10        |              0.015 |             1.315 |      0.5      |      0.03     |                       5 | 2024-12-28 23:43:27.072186880 |           10        |  1.297     |  0.000125  |         0.03     |   1.33     |     1.27513   |
|            4 |     1.3       |             10        |              0.015 |             1.315 |      0.5      |      0.03     |                       5 | 2024-12-28 23:43:27.072205    |           10        |  1.297     |  0.005     |         0.03     |   1.33     |     1.305     |
|          nan |     0.0957427 |              5.03322  |            nan     |           nan     |      0.282931 |      0.011547 |                     nan | nan                           |            5.03322  |  0.0978076 |  0.0137886 |         0.011547 |   0.106301 |     0.0844993 |
## Trades
![Trade Outcomes](trade_outcomes.png)
This plot shows the distribution of trade outcomes (win/loss).
![Return Distribution](return_distribution.png)
This plot shows the distribution of returns for the trades. The histogram provides a visual representation of the frequency of different return values.
## DataFrame
|   trade_uid |   confidence |   entry_price |   initial_risk_reward | type_3_m15   |   potential_return | management_strategy   |   potential_price | session   |   SL_distance |   TP_distance |   potential_risk_reward | entry_time                 |   risk_reward_ratio |   sl_price | side   | type_2_h1   |   return | outcome   |   initial_return | type_1_m1   |   tp_price | htf_poi_ltf_confirmation   |   close_price |
|------------:|-------------:|--------------:|----------------------:|:-------------|-------------------:|:----------------------|------------------:|:----------|--------------:|--------------:|------------------------:|:---------------------------|--------------------:|-----------:|:-------|:------------|---------:|:----------|-----------------:|:------------|-----------:|:---------------------------|--------------:|
|           1 |          nan |           1.1 |              2        | True         |            nan     | no_management         |           nan     | tokyo     |         0.005 |          0.01 |                     nan | 2024-12-28 23:43:27.072181 |            2        |      1.095 | long   |             | nan      |           |             0.01 | True        |       1.11 |                            |      nan      |
|           2 |          nan |           1.2 |              0.666667 |              |            nan     | no_management         |           nan     | tokyo     |         0.015 |          0.01 |                     nan | 2024-12-28 23:43:27.072205 |            0.666667 |      1.185 | long   | True        |  -0.0145 | loss      |             0.01 |             |       1.21 | True                       |        1.1855 |
|           3 |          nan |           1.3 |             10        |              |            nan     | no_management         |           nan     | london    |         0.5   |          0.03 |                     nan | 2024-12-27 10:00:01        |           10        |      1.297 | long   |             | nan      |           |             0.03 |             |       1.33 | False                      |      nan      |
|           4 |            4 |           1.3 |             10        |              |              0.015 | strategy_2            |             1.315 | london    |         0.5   |          0.03 |                       5 | 2024-12-25 10:00:00        |           10        |      1.297 | long   |             |   0.005  | win       |             0.03 |             |       1.33 | False                      |        1.305  |
- [Trade 1](trade_1.md)
- [Trade 2](trade_2.md)
- [Trade 3](trade_3.md)
- [Trade 4](trade_4.md)