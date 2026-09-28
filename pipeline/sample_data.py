"""Generate a realistic sample CRM export for demos and tests."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

STAGES = ["Lead", "Qualified", "Demo", "Proposal", "Negotiation"]
REPS = ["Aarav", "Diya", "Kabir", "Meera", "Rohan"]
SOURCES = ["Inbound", "Outbound", "Referral", "Event", "Partner"]
INDUSTRIES = ["SaaS", "Retail", "Healthcare", "Manufacturing", "Education"]

# How far a deal gets before it closes, and the chance of a win from there.
SOURCE_WIN_BIAS = {"Referral": 0.15, "Partner": 0.08, "Inbound": 0.05, "Event": 0.0, "Outbound": -0.07}


def generate(n=400, seed=42, today=date(2026, 9, 30)):
    rng = random.Random(seed)
    rows = []
    for i in range(1, n + 1):
        created = today - timedelta(days=rng.randint(5, 270))
        source = rng.choice(SOURCES)
        amount = round(rng.lognormvariate(11.2, 0.6), -3)  # typically ₹50k-₹2L
        furthest = rng.choices(range(len(STAGES)), weights=[30, 25, 20, 15, 10])[0]
        age = (today - created).days

        closed = age > 45 and rng.random() < 0.75
        if closed:
            p_win = 0.18 + 0.1 * furthest + SOURCE_WIN_BIAS[source]
            status = "Won" if rng.random() < p_win else "Lost"
            close_date = created + timedelta(days=rng.randint(20, max(21, age)))
            stage = STAGES[furthest]
        else:
            status = "Open"
            close_date = ""
            stage = STAGES[furthest]

        rows.append({
            "deal_id": f"D{i:04d}",
            "company": f"Company {i:03d}",
            "industry": rng.choice(INDUSTRIES),
            "owner": rng.choice(REPS),
            "source": source,
            "stage": stage,
            "status": status,
            "amount": int(amount),
            "created_date": created.isoformat(),
            "close_date": close_date.isoformat() if close_date else "",
        })
    return rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    out = write_csv(Path(__file__).resolve().parent.parent / "data" / "sample_deals.csv", generate())
    print(f"Wrote {out}")
