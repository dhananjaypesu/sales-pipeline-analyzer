"""Command-line entry point: prints a pipeline report or writes it as Markdown."""
import argparse
from datetime import date
from pathlib import Path

from . import metrics


def inr(x):
    """Format a number as Indian rupees with lakh/crore shorthand."""
    if abs(x) >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if abs(x) >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return f"₹{x:,.0f}"


def pct(x):
    return f"{x * 100:.1f}%"


def md_table(df, formats):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        cells = [formats.get(c, str)(row[c]) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_report(df, today, stale_days=60):
    s = metrics.summarize(df)
    fc = metrics.forecast(df)
    money = {k: inr for k in ("won_revenue", "open_pipeline", "pipeline", "weighted", "amount")}
    rates = {k: pct for k in ("win_rate", "conversion_from_prev", "share_of_total", "weight")}
    fmt = {**money, **rates}

    stale = metrics.stale_deals(df, today, stale_days)
    parts = [
        "# Sales Pipeline Report",
        f"_Generated {today.isoformat()} from {s.total_deals} deals_",
        "",
        "## Headline numbers",
        "",
        f"- **Win rate:** {pct(s.win_rate)} ({s.won_deals} won / {s.lost_deals} lost)",
        f"- **Won revenue:** {inr(s.won_revenue)}",
        f"- **Open pipeline:** {inr(s.open_pipeline)} across {s.open_deals} deals",
        f"- **Weighted forecast:** {inr(fc.weighted.sum())}",
        f"- **Average won deal:** {inr(s.avg_deal_won)}",
        f"- **Average sales cycle:** {s.avg_cycle_days:.0f} days",
        "",
        "## Funnel",
        "",
        md_table(metrics.funnel(df), fmt),
        "",
        "## By sales rep",
        "",
        md_table(metrics.breakdown(df, "owner"), fmt),
        "",
        "## By lead source",
        "",
        md_table(metrics.breakdown(df, "source"), fmt),
        "",
        "## Weighted forecast",
        "",
        md_table(fc, fmt),
        "",
        f"## Stale deals (open > {stale_days} days)",
        "",
        md_table(stale.head(10), fmt) if len(stale) else "_None._",
        "",
    ]
    return "\n".join(parts)


def main(argv=None):
    p = argparse.ArgumentParser(description="Analyze a CRM deals export (CSV).")
    p.add_argument("csv", type=Path, help="path to deals CSV")
    p.add_argument("-o", "--output", type=Path, help="write the Markdown report to this file")
    p.add_argument("--stale-days", type=int, default=60, help="age threshold for stale open deals")
    p.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                   help="report date, YYYY-MM-DD (default: today)")
    args = p.parse_args(argv)

    df = metrics.load_deals(args.csv)
    report = build_report(df, args.as_of, args.stale_days)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
