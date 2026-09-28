"""Core pipeline metrics computed from a CRM deals export."""
from dataclasses import dataclass

import pandas as pd

STAGES = ["Lead", "Qualified", "Demo", "Proposal", "Negotiation"]
REQUIRED = {"deal_id", "owner", "source", "stage", "status", "amount", "created_date", "close_date"}

# Default probability that an open deal at each stage eventually closes won.
DEFAULT_STAGE_WEIGHTS = {"Lead": 0.10, "Qualified": 0.20, "Demo": 0.35, "Proposal": 0.55, "Negotiation": 0.75}


def load_deals(path):
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

    df["status"] = df["status"].str.strip().str.title()
    bad_status = set(df["status"]) - {"Open", "Won", "Lost"}
    if bad_status:
        raise ValueError(f"Unknown status values: {', '.join(sorted(bad_status))}")
    bad_stage = set(df["stage"]) - set(STAGES)
    if bad_stage:
        raise ValueError(f"Unknown stage values: {', '.join(sorted(bad_stage))}")

    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    df["created_date"] = pd.to_datetime(df["created_date"])
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
    df["stage_idx"] = df["stage"].map(STAGES.index)
    return df


@dataclass
class Summary:
    total_deals: int
    open_deals: int
    won_deals: int
    lost_deals: int
    win_rate: float          # won / (won + lost)
    won_revenue: float
    open_pipeline: float
    avg_deal_won: float
    avg_cycle_days: float    # created -> close, won deals


def summarize(df):
    won = df[df.status == "Won"]
    lost = df[df.status == "Lost"]
    open_ = df[df.status == "Open"]
    closed = len(won) + len(lost)
    cycle = (won.close_date - won.created_date).dt.days
    return Summary(
        total_deals=len(df),
        open_deals=len(open_),
        won_deals=len(won),
        lost_deals=len(lost),
        win_rate=len(won) / closed if closed else 0.0,
        won_revenue=float(won.amount.sum()),
        open_pipeline=float(open_.amount.sum()),
        avg_deal_won=float(won.amount.mean()) if len(won) else 0.0,
        avg_cycle_days=float(cycle.mean()) if len(won) else 0.0,
    )


def funnel(df):
    """How many deals reached each stage, and stage-to-stage conversion."""
    reached = [(df.stage_idx >= i).sum() for i in range(len(STAGES))]
    rows = []
    for i, stage in enumerate(STAGES):
        prev = reached[i - 1] if i else reached[0]
        rows.append({
            "stage": stage,
            "deals_reached": int(reached[i]),
            "conversion_from_prev": reached[i] / prev if prev else 0.0,
            "share_of_total": reached[i] / reached[0] if reached[0] else 0.0,
        })
    return pd.DataFrame(rows)


def breakdown(df, by):
    """Win rate, revenue and pipeline grouped by a column (owner, source, ...)."""
    def agg(g):
        won = g[g.status == "Won"]
        closed = g[g.status != "Open"]
        return pd.Series({
            "deals": len(g),
            "won": len(won),
            "win_rate": len(won) / len(closed) if len(closed) else 0.0,
            "won_revenue": won.amount.sum(),
            "open_pipeline": g[g.status == "Open"].amount.sum(),
        })

    out = df.groupby(by).apply(agg, include_groups=False).reset_index()
    out[["deals", "won"]] = out[["deals", "won"]].astype(int)
    return out.sort_values("won_revenue", ascending=False).reset_index(drop=True)


def forecast(df, weights=None):
    """Weighted forecast of open pipeline by stage."""
    weights = weights or DEFAULT_STAGE_WEIGHTS
    open_ = df[df.status == "Open"]
    rows = []
    for stage in STAGES:
        s = open_[open_.stage == stage]
        rows.append({
            "stage": stage,
            "open_deals": len(s),
            "pipeline": float(s.amount.sum()),
            "weight": weights[stage],
            "weighted": float(s.amount.sum()) * weights[stage],
        })
    return pd.DataFrame(rows)


def stale_deals(df, today, days=60):
    """Open deals older than `days` — candidates for follow-up or cleanup."""
    open_ = df[df.status == "Open"].copy()
    open_["age_days"] = (pd.Timestamp(today) - open_.created_date).dt.days
    return (open_[open_.age_days > days]
            .sort_values("amount", ascending=False)
            [["deal_id", "owner", "stage", "amount", "age_days"]]
            .reset_index(drop=True))
