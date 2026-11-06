# 🎾 Tennis Intelligence 360 — SportRadar → SQL → Streamlit
**Author:** P Suman Sangeet · PGDM (Big Data Analytics) · Data Science & AI

End-to-end data project: collect tennis data from the Sportradar API, store it in a normalised SQL warehouse, analyse it with 20 SQL queries and explore it in an interactive Streamlit app.

## Deliverables
| # | Deliverable | File(s) |
|---|---|---|
| 1 | SQL database (6 tables, PK/FK, indexes) | `schema.sql`, built by `etl.py` |
| 2 | API scripts (extract → transform → load) | `etl.py` |
| 3 | Streamlit app (12 pages) | `app.py`, `.streamlit/config.toml` |
| 4 | Documentation + all SQL queries | `README.md`, `sql_queries.sql`, in-app **Project Report** page (9 interactive sections) |

## Quick start
```bash
pip install -r requirements.txt
export SPORTRADAR_API_KEY=...            # developer.sportradar.com (trial key)
export DB_URL=mysql+pymysql://user:pass@localhost/tennis   # optional; default sqlite:///tennis.db
python etl.py                            # or: python etl.py --only rankings
streamlit run app.py
```
Deploy: Streamlit Community Cloud → `app.py` → Secrets: `DB_URL = "..."` (database must be internet-reachable).

## Workflow
1. **Extract** – `requests` session, exponential back-off, `Retry-After`, 1.2 s pacing (trial quota ≈ 1 req/s).
2. **Transform** – nested JSON flattened per endpoint; defaults for missing fields; de-duplication on primary keys.
3. **Load** – one transaction per run; dimension tables replaced, rankings replaced per (board, year, week) → idempotent, history accumulates.
4. **Analyse** – 20 SQL queries (`sql_queries.sql`).
5. **Serve** – Streamlit reads the DB live (60 s cache) with a read-only SQL guard.

## Schema
```
categories 1─N competitions (self-reference: parent_id)
complexes  1─N venues
competitors 1─N competitor_rankings (rank, movement, points, competitions_played, ranking_name, year, week)
```
Normalised to 3NF; indexes on every foreign key plus `venues.country_name`, `competitors.country`, `(year, week)`.

## App pages
Recruiter Showcase · Dashboard · Search & Filter · Competitor Profile · Country Analysis · Leaderboards · Advanced Analytics (Lorenz/Gini, tiers, efficiency quadrant, correlations) · Competitions · Venues · Data Quality (8 live integrity checks) · Project Report · SQL Lab.

## Challenges & solutions
| Challenge | Solution |
|---|---|
| API rate limit (HTTP 429) | Retry with back-off + pacing |
| Deeply nested JSON | Per-endpoint flatteners with safe defaults |
| Nulls vs NOT NULL constraints | Explicit defaults (`Unknown`, `UTC`, 0) |
| `rank` reserved word | Dialect-aware quoting |
| Re-runs creating duplicates | Idempotent delete-then-insert |
| Arbitrary SQL in the app | SELECT/WITH whitelist + keyword blocklist |

## Insights
Open the **Recruiter Showcase** and **Advanced Analytics** pages — headline findings (points concentration/Gini, deepest nation, most efficient player, doubles/women's share of competitions, venue coverage) are computed live from the database, so they stay correct as new weekly snapshots load. Paste your final numbers here before submitting.

## Testing
ETL tested with mocked API payloads (loads, FK integrity, second run produces no duplicates); all app pages smoke-tested with `streamlit.testing.AppTest`.
