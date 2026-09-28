# Sales Pipeline Analyzer

A Python CLI that turns a CRM deals export (CSV) into the numbers a sales team actually looks at: win rate, funnel conversion, rep and lead-source performance, a weighted revenue forecast, and a list of stale deals that need follow-up. Output is a clean Markdown report.

Amounts are reported in Indian rupees with lakh/crore shorthand (₹2.50 L, ₹1.16 Cr).

## What it calculates

| Section | What it tells you |
|---|---|
| Headline numbers | Win rate, won revenue, open pipeline, weighted forecast, average deal size, average sales cycle |
| Funnel | How many deals reached each stage and the conversion between stages |
| By sales rep | Deals, wins, win rate, revenue and open pipeline per rep |
| By lead source | Which channels (referral, inbound, events…) actually convert |
| Weighted forecast | Open pipeline × stage probability, per stage |
| Stale deals | Open deals older than N days, largest first |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# run on the bundled sample data
python -m pipeline.cli data/sample_deals.csv --as-of 2026-09-30

# or save the report
python -m pipeline.cli data/sample_deals.csv -o report.md
```

See [`sample_report.md`](sample_report.md) for example output.

## Input format

One row per deal:

| Column | Example | Notes |
|---|---|---|
| `deal_id` | D0001 | |
| `owner` | Diya | Sales rep |
| `source` | Referral | Any lead source label |
| `stage` | Proposal | Furthest stage reached: Lead, Qualified, Demo, Proposal, Negotiation |
| `status` | Open | Open, Won or Lost |
| `amount` | 120000 | Deal value |
| `created_date` | 2026-03-14 | YYYY-MM-DD |
| `close_date` | 2026-05-02 | Blank for open deals |

Extra columns (industry, company, …) are ignored, so most CRM exports work after renaming a few headers.

## Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output` | print to terminal | Write the report to a Markdown file |
| `--stale-days` | 60 | Age threshold for stale open deals |
| `--as-of` | today | Report date (YYYY-MM-DD) |

Stage probabilities for the forecast live in `DEFAULT_STAGE_WEIGHTS` in `pipeline/metrics.py`; tune them to your team's history.

## Sample data

`data/sample_deals.csv` holds 400 synthetic deals. Regenerate it with:

```bash
python -m pipeline.sample_data
```

## Tests

```bash
pytest
```

## Project structure

```
pipeline/
  metrics.py       # loading, validation and all calculations
  cli.py           # argument parsing and Markdown report
  sample_data.py   # synthetic CRM data generator
data/
  sample_deals.csv
tests/
  test_metrics.py
```

## Ideas for extending it

- Charts (funnel and rep leaderboard) exported as PNGs
- Month-over-month trend of win rate and pipeline created
- Learn stage weights from historical closed deals instead of fixed values
- A small Streamlit or Flask dashboard on top of `metrics.py`
