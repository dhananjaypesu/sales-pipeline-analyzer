from datetime import date

import pandas as pd
import pytest

from pipeline import metrics
from pipeline.cli import build_report, inr
from pipeline.sample_data import generate, write_csv


@pytest.fixture
def df(tmp_path):
    rows = [
        {"deal_id": "A", "owner": "X", "source": "Inbound", "stage": "Negotiation", "status": "Won",
         "amount": 100000, "created_date": "2026-01-01", "close_date": "2026-01-31"},
        {"deal_id": "B", "owner": "X", "source": "Outbound", "stage": "Demo", "status": "Lost",
         "amount": 50000, "created_date": "2026-01-10", "close_date": "2026-02-10"},
        {"deal_id": "C", "owner": "Y", "source": "Inbound", "stage": "Proposal", "status": "Open",
         "amount": 200000, "created_date": "2026-03-01", "close_date": ""},
        {"deal_id": "D", "owner": "Y", "source": "Referral", "stage": "Lead", "status": "Open",
         "amount": 40000, "created_date": "2026-05-01", "close_date": ""},
    ]
    path = tmp_path / "deals.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return metrics.load_deals(path)


def test_summary(df):
    s = metrics.summarize(df)
    assert s.win_rate == 0.5
    assert s.won_revenue == 100000
    assert s.open_pipeline == 240000
    assert s.avg_cycle_days == 30


def test_funnel_counts(df):
    f = metrics.funnel(df).set_index("stage")
    assert f.loc["Lead", "deals_reached"] == 4
    assert f.loc["Demo", "deals_reached"] == 3
    assert f.loc["Proposal", "deals_reached"] == 2
    assert f.loc["Negotiation", "deals_reached"] == 1


def test_forecast(df):
    fc = metrics.forecast(df).set_index("stage")
    assert fc.loc["Proposal", "weighted"] == pytest.approx(200000 * 0.55)
    assert fc.loc["Lead", "weighted"] == pytest.approx(40000 * 0.10)


def test_breakdown_by_owner(df):
    b = metrics.breakdown(df, "owner").set_index("owner")
    assert b.loc["X", "win_rate"] == 0.5
    assert b.loc["Y", "open_pipeline"] == 240000


def test_stale(df):
    stale = metrics.stale_deals(df, date(2026, 6, 15), days=60)
    assert list(stale.deal_id) == ["C"]


def test_rejects_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame([{"deal_id": 1}]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        metrics.load_deals(path)


def test_inr_format():
    assert inr(5000) == "₹5,000"
    assert inr(250000) == "₹2.50 L"
    assert inr(35000000) == "₹3.50 Cr"


def test_full_report_on_sample(tmp_path):
    path = write_csv(tmp_path / "sample.csv", generate(n=200))
    report = build_report(metrics.load_deals(path), date(2026, 9, 30))
    assert "# Sales Pipeline Report" in report
    assert "## By sales rep" in report
