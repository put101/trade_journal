import trade


def test_full_close_profit_long():
    t = trade.Trade(
        entry_price=100,
        size=2,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=90,
        tp_price=130,
        sl_monetary_value=-20,
    )
    t.close_position(exit_price=110, exit_time="2025-01-01 11:00")
    df = t.get_state_history()
    # profit = (110-100)*2*point_value ; point_value inferred from sl_monetary_value
    # sl_monetary_value= -20 over 10 points on size=2 -> pv = 1.0
    assert t.current_size == 0
    last = df.iloc[-1]
    assert abs(last.realised_profit - 20) < 1e-9


def test_partial_then_full_close():
    t = trade.Trade(
        entry_price=50,
        size=4,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=45,
        tp_price=70,
        sl_monetary_value=-20,
    )
    t.close_position(exit_price=55, exit_time="2025-01-01 10:30", size=1)
    assert t.current_size == 3
    t.close_position(exit_price=60, exit_time="2025-01-01 11:00")
    assert t.current_size == 0
    df = t.get_state_history()
    # point value: 20 monetary risk over 5 points * 4 size => pv = 1.0
    # first close profit: (55-50)*1*1 = 5
    # second close profit: (60 - avg_entry_price)*3 -> avg still 50 -> 10*3=30 ; total 35
    assert abs(df.iloc[-1].realised_profit - 35) < 1e-9


def test_relative_exec_size():
    t = trade.Trade(
        entry_price=10,
        size=1,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=9,
        tp_price=20,
        sl_monetary_value=-1,
    )
    t.add_position(entry_price=11, size=1, entry_time="2025-01-01 10:05")
    t.close_position(exit_price=12, exit_time="2025-01-01 10:10", size=1)
    t.close_position(exit_price=13, exit_time="2025-01-01 10:15")
    df = t.get_state_history()
    assert "exec_size_rel" in df.columns
    # The first partial close exec_size_rel should be 1 / 2 = 0.5
    part_row = df[df.act == trade.Act.PART.value].iloc[0]
    assert abs(part_row.exec_size_rel - 0.5) < 1e-9


def test_close_size_exceeds_current():
    t = trade.Trade(
        entry_price=10,
        size=1,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=9,
        tp_price=20,
        sl_monetary_value=-1,
    )
    try:
        t.close_position(exit_price=11, exit_time="2025-01-01 10:10", size=2)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_plot_returns_chart():
    t = trade.Trade(
        entry_price=10,
        size=1,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=9,
        tp_price=20,
        sl_monetary_value=-1,
    )
    t.close_position(exit_price=11, exit_time="2025-01-01 10:10")
    chart = t.plot_trade_levels_altair()
    assert chart is not None


def test_realised_profit_rr():
    # risk: entry 100, SL 95, size 2, sl_monetary_value -20 => risk per point = 20 / (5*2)=2, point_value=2
    # initial risk monetary = 20
    t = trade.Trade(
        entry_price=100,
        size=2,
        entry_time="2025-01-01 10:00",
        side="long",
        sl_price=95,
        tp_price=130,
        sl_monetary_value=-20,
    )
    # close half at +3 points (103) size 1 => profit = 3 * 1 * 2 = 6 (0.3R)
    t.close_position(exit_price=103, exit_time="2025-01-01 10:05", size=1)
    # close rest at +5 points (105) size 1 => profit added = 5 * 1 * 2 = 10; total 16 => 0.8R
    t.close_position(exit_price=105, exit_time="2025-01-01 10:10")
    df = t.get_state_history()
    rr = df.iloc[-1]["realised_profit_rr"]
    assert abs(rr - 0.8) < 1e-9
