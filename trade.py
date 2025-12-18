"""Trade journal module — richer plotting

Changes in this version
-----------------------
* **Improved interactive chart**
  * Event markers (shape‑coded by `Act`) plotted at the execution price.
  * Hover tooltips show action, sizes, prices and realised P&L.
  * Optional text labels for CLOSE events.
* `plot_trade_levels_altair()` now builds a layered Altair chart:
  * Top panel: price levels + event points.
  * Bottom panel: realised P&L over time.

The data model (State snapshots) is unchanged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

import altair as alt
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

Number = float


# ---------------------------------------------------------------------------
# Enums are strings ➜ auto‑serialisable to JSON
# ---------------------------------------------------------------------------
class Side(str, Enum):
    LONG = "long"
    SHORT = "short"


class Act(str, Enum):
    ADD = "add_position"
    PART = "partial_close"
    CLOSE = "close_trade"
    SLTP = "modify_sl_tp"
    INIT = "initial_trade"


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Lot:
    price: Number
    size: Number


REASONS_NO_REASON_PROVIDED = "NO_REASON_PROVIDED"


@dataclass
class Event:
    time: pd.Timestamp
    act: Act
    size: Number = 0
    price: Optional[Number] = None
    sl: Optional[Number] = None
    tp: Optional[Number] = None
    profit: Number = 0.0
    reason: str = REASONS_NO_REASON_PROVIDED
    commission: Number = 0.0


@dataclass
class State:
    time: pd.Timestamp
    act: Act
    exec_size: Number
    exec_price: Optional[Number]
    reason: Optional[str]
    current_size: Number
    avg_entry_price: Number
    sl_price: Number
    tp_price: Number
    event_profit: Number
    realised_profit: Number
    side: Side
    point_value: Number
    commission: Number = 0.0


# ---------------------------------------------------------------------------
# Trade object
# ---------------------------------------------------------------------------
class Trade:
    """Trade object with enriched plotting and FIXED edge‑cases."""

    def __init__(
        self,
        entry_price: Number,
        size: Number,
        entry_time: str | datetime,
        side: str,
        sl_price: Number,
        tp_price: Number,
        sl_monetary_value: Number,
        point_value: Number | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.side: Side = Side(side.lower())
        self.initial_risk_monetary: float | None = None  # for R multiple normalisation

        # Determine point_value and initial risk
        if point_value is not None:
            self.point_value = float(point_value)
        elif sl_monetary_value is not None:
            # risk per point per size
            self.point_value = float(
                abs(sl_monetary_value) / abs(entry_price - sl_price) / size
            )
            self.initial_risk_monetary = float(abs(sl_monetary_value))
        else:
            inferred = infer_point_value(
                entry_price=entry_price,
                exit_price=kwargs.get("exit_price"),
                size=size,
                profit=kwargs.get("profit"),
                commission=kwargs.get("commission", 0.0),
            )
            self.point_value = float(inferred) if inferred == inferred else 1.0
            try:
                self.initial_risk_monetary = (
                    abs(entry_price - sl_price) * self.point_value * size
                )
            except Exception:
                self.initial_risk_monetary = None

        self._lots: List[Lot] = [Lot(entry_price, size)]
        self.events: List[Event] = []
        self._states: List[State] = []
        self._realised_profit: Number = 0.0

        # seed first snapshot
        self._apply(
            Event(
                pd.Timestamp(entry_time),
                Act.INIT,
                size,
                entry_price,
                sl_price,
                tp_price,
                commission=kwargs.get("commission", 0.0),
            )
        )
        self.args = args
        self.kwargs = kwargs
        print(self)

    # ---------- derived properties ----------------------------------------
    @property
    def current_size(self) -> Number:
        return sum(lot_obj.size for lot_obj in self._lots)

    @property
    def avg_entry_price(self) -> Number:
        tot = sum(lot_obj.price * lot_obj.size for lot_obj in self._lots)
        return tot / self.current_size if self.current_size else float("nan")
        # NaN avoids the ugly drop‑to‑zero once we are flat

    @property
    def sl_price(self) -> Number:
        for ev in reversed(self.events):
            if ev.sl is not None:
                return ev.sl
        return float("nan")

    @property
    def tp_price(self) -> Number:
        for ev in reversed(self.events):
            if ev.tp is not None:
                return ev.tp
        return float("nan")

    # ---------- public API -------------------------------------------------
    def add_position(self, entry_price: Number, size: Number, entry_time, **kw):
        self._apply(Event(pd.Timestamp(entry_time), Act.ADD, size, entry_price, **kw))

    def close_position(
        self, exit_price: Number, exit_time, size: Optional[Number] = None, **kw
    ) -> None:
        # Determine effective close size & act type
        current = self.current_size
        if current <= 0:
            raise ValueError("No open position to close.")

        if size is not None:
            # basic validation
            if size <= 0:
                raise ValueError("Close size must be positive.")
            if size - current > 1e-12:  # allow tiny fp tolerance
                raise ValueError(
                    f"Requested close size {size} exceeds current position {current}."
                )

        # If size omitted OR equals (within tol) the whole position ➜ full close
        full_close = size is None or (size is not None and abs(size - current) < 1e-12)
        eff_size: Number = current if full_close else float(size)  # type: ignore[arg-type]
        act = Act.CLOSE if full_close else Act.PART

        self._apply(
            Event(
                pd.Timestamp(exit_time),
                act,
                eff_size,
                exit_price,
                **kw,
            )
        )

    def modify_sl_tp(self, modification_time, new_sl=None, new_tp=None):
        self._apply(
            Event(pd.Timestamp(modification_time), Act.SLTP, 0, sl=new_sl, tp=new_tp)
        )

    # ---------- internals --------------------------------------------------
    def _apply(self, ev: Event) -> None:
        print(
            f"Applying event: {ev.act} at {ev.time} with size {ev.size} and price {ev.price}"
        )

        if ev.act is Act.ADD:
            if ev.price is None:
                raise ValueError("ADD event requires a price")
            self._lots.append(Lot(ev.price, ev.size))
        elif ev.act in (Act.PART, Act.CLOSE):
            remaining = ev.size

            # Save avg_entry_price BEFORE modifying lots
            avg_price = self.avg_entry_price

            if remaining - self.current_size > 1e-12:
                raise ValueError(
                    f"Attempting to close {remaining} but only {self.current_size} open."
                )

            while remaining and self._lots:
                lot = self._lots[0]
                take = min(remaining, lot.size)
                lot.size -= take
                remaining -= take
                if lot.size == 0:
                    self._lots.pop(0)

            if ev.price is None:
                raise ValueError("Close/partial close requires an execution price")
            ev.profit = (
                (ev.price - avg_price)
                * ev.size
                * float(self.point_value)
                * (1 if self.side is Side.LONG else -1)
            )

        print(f"Event profit calculated: {ev.profit}")

        self.events.append(ev)

        self._realised_profit = sum(
            e.profit - e.commission
            for e in self.events
            if e.act in (Act.PART, Act.CLOSE)
        )

        self._states.append(
            State(
                time=ev.time,
                act=ev.act,
                exec_size=ev.size,
                exec_price=ev.price,
                reason=ev.reason,
                current_size=self.current_size,
                avg_entry_price=self.avg_entry_price,
                sl_price=self.sl_price,
                tp_price=self.tp_price,
                event_profit=ev.profit,
                realised_profit=self._realised_profit,
                side=self.side,
                point_value=self.point_value,
                commission=ev.commission,
            )
        )

    # ---------- dataframe --------------------------------------------------
    def get_state_history(self) -> pd.DataFrame:
        df = pd.DataFrame(asdict(s) for s in self._states)
        if not df.empty:
            max_pos = df["current_size"].max() or 1.0
            # Relative executed size vs max position attained
            df["exec_size_rel"] = df["exec_size"].abs() / max_pos
            # R-multiple normalisation (realised & event) if risk known
            if self.initial_risk_monetary and self.initial_risk_monetary != 0:
                df["realised_profit_rr"] = (
                    df["realised_profit"] / self.initial_risk_monetary
                )
                df["event_profit_rr"] = df["event_profit"] / self.initial_risk_monetary
            else:
                df["realised_profit_rr"] = float("nan")
                df["event_profit_rr"] = float("nan")
        return df

    # Backwards compatible helper (not previously present but referenced in notebook)
    def get_trade_summary(self) -> List[dict]:
        """Return list of state snapshots (dicts)."""
        return [asdict(s) for s in self._states]

    # ---------- plotting ---------------------------------------------------
    def plot_trade_levels_altair(self) -> alt.TopLevelMixin:
        """Interactive trade chart with improved marker visibility and hover hit area."""
        df = self.get_state_history()
        if df.empty:
            raise ValueError("No state history to plot.")

        base = alt.Chart(df).encode(x=alt.X("time:T", title="Time"))

        price_cols = {
            "avg_entry_price": "#1f77b4",
            "sl_price": "#d62728",
            "tp_price": "#2ca02c",
        }
        price_lines = (
            base.transform_fold(list(price_cols), as_=["level", "value"])
            .mark_line(strokeWidth=2)
            .encode(
                y=alt.Y("value:Q", title="Price Level", scale=alt.Scale(zero=False)),
                color=alt.Color(
                    "level:N",
                    title="Price Levels",
                    scale=alt.Scale(
                        domain=list(price_cols), range=list(price_cols.values())
                    ),
                ),
            )
        )

        event_points_main = (
            base.transform_filter("datum.exec_price != null")
            .mark_point(filled=True, stroke="black", strokeWidth=2.0, opacity=0.95)
            .encode(
                y="exec_price:Q",
                shape=alt.Shape(
                    "act:N",
                    legend=alt.Legend(title="Event"),
                    scale=alt.Scale(
                        domain=[a.value for a in Act],
                        range=["triangle-up", "circle", "cross", "diamond", "square"],
                    ),
                ),
                size=alt.Size(
                    "exec_size_rel:Q",
                    legend=None,
                    scale=alt.Scale(domain=[0, 1], range=[180, 900]),
                ),
                color=alt.Color("act:N", legend=None),
                tooltip=[
                    alt.Tooltip("act:N", title="Action"),
                    alt.Tooltip("exec_size:Q", title="Size"),
                    alt.Tooltip("exec_size_rel:Q", title="Rel Size", format=".2f"),
                    alt.Tooltip("exec_price:Q", title="Exec Price"),
                    alt.Tooltip("realised_profit:Q", title="Cum. P&L"),
                    alt.Tooltip("commission:Q", title="Commission"),
                    alt.Tooltip("reason:N", title="Reason"),
                    alt.Tooltip("time:T", title="Time"),
                ],
            )
        )

        event_points_hover = (
            base.transform_filter("datum.exec_price != null")
            .mark_point(filled=True, opacity=0, size=1600)
            .encode(
                y="exec_price:Q",
                tooltip=[
                    alt.Tooltip("act:N", title="Action"),
                    alt.Tooltip("exec_size:Q", title="Size"),
                    alt.Tooltip("exec_size_rel:Q", title="Rel Size", format=".2f"),
                    alt.Tooltip("exec_price:Q", title="Exec Price"),
                    alt.Tooltip("realised_profit:Q", title="Cum. P&L"),
                    alt.Tooltip("commission:Q", title="Commission"),
                    alt.Tooltip("reason:N", title="Reason"),
                    alt.Tooltip("time:T", title="Time"),
                ],
            )
        )

        close_text = (
            base.transform_filter("datum.act == 'close_trade'")
            .mark_text(align="left", dx=6, dy=-6, fontSize=11, fontWeight="bold")
            .encode(y="exec_price:Q", text=alt.value("CLOSE"))
        )

        price_panel = (
            price_lines + event_points_hover + event_points_main + close_text
        ).properties(height=320)

        # Combined monetary and R-multiple realised P&L panel (dual y axes)
        pnl_line = base.mark_line(
            strokeDash=[6, 4], strokeWidth=2, color="#ffbf00"
        ).encode(
            y=alt.Y(
                "realised_profit:Q", axis=alt.Axis(title="Realised P&L", orient="left")
            ),
            tooltip=[
                alt.Tooltip("realised_profit:Q", title="Cum. P&L"),
                alt.Tooltip("time:T", title="Time"),
            ],
        )
        has_rr = df["realised_profit_rr"].notna().any()
        if has_rr:
            rr_line = base.mark_line(strokeWidth=2, color="#6a3d9a").encode(
                y=alt.Y(
                    "realised_profit_rr:Q",
                    axis=alt.Axis(title="Realised P&L (R)", orient="right"),
                ),
                tooltip=[
                    alt.Tooltip(
                        "realised_profit_rr:Q", title="Cum. P&L (R)", format=".2f"
                    ),
                    alt.Tooltip("realised_profit:Q", title="Cum. P&L"),
                    alt.Tooltip("time:T", title="Time"),
                ],
            )
            pnl_panel = (
                alt.layer(pnl_line, rr_line)
                .resolve_scale(y="independent")
                .properties(height=200)
            )
        else:
            pnl_panel = pnl_line.properties(height=200)

        chart = (
            alt.vconcat(price_panel, pnl_panel)
            .resolve_scale(y="independent")
            .configure_axis(grid=True)
            .configure_view(stroke="transparent")
        )
        return chart

    def plot_trade_network(self) -> None:
        """
        Plot a network graph of trade events and their transitions over time.
        """
        # Create a directed graph
        G = nx.DiGraph()

        # Add nodes and edges based on events
        for i, event in enumerate(self.events):
            node_label = (
                f"{event.act.value}\n{event.time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            G.add_node(i, label=node_label, act=event.act.value, time=event.time)

            if i > 0:
                G.add_edge(i - 1, i)

        # Draw the graph
        pos = nx.spring_layout(G, seed=42)  # Layout for consistent positioning
        plt.figure(figsize=(12, 8))

        # Draw nodes with labels
        node_labels = nx.get_node_attributes(G, "label")
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color="lightblue")
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)

        # Draw edges
        nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, edge_color="gray")

        # Add a title
        plt.title("Trade Events Network Graph", fontsize=14)
        plt.axis("off")
        plt.show()

    def to_trade_row(self) -> dict:
        """
        Convert the Trade object into a dictionary representation for use in DataFrames or other structures.
        """
        trade_row = {
            "entry_price": self._states[0].avg_entry_price if self._states else None,
            "sl_price": self.sl_price,
            "tp_price": self.tp_price,
            "max_size": max(s.current_size for s in self._states)
            if self._states
            else None,
            "entry_size": self._states[0].current_size if self._states else None,
            "current_size": self.current_size,
            "realised_profit": self._realised_profit,
            "side": self.side.value,
            "point_value": self.point_value,
            "entry_time": self._states[0].time if self._states else None,
            "events": [asdict(event) for event in self.events],
        }
        return trade_row


def infer_point_value(
    entry_price: float,
    exit_price: float,
    size: float,
    profit: float,
    delta: float = 0.0,
    *args,
    **kwargs,
) -> float:
    """
    Infer point value from trade stats.

    Parameters
    ----------
    entry_price : float
        Entry price of the position.
    exit_price : float
        Exit price of the position.
    size : float
        Position size (lot).
    profit : float
        Total profit of the trade (positive or negative).
    commission : float, optional
        Total commission paid (negative number or 0).

    Returns
    -------
    point_value : float
        The monetary value per point/pip.
    """
    if delta == 0.0:
        delta = exit_price - entry_price

    if delta == 0 or size == 0:
        return float("nan")  # Avoid division by zero

    return (profit) / (delta * size)
