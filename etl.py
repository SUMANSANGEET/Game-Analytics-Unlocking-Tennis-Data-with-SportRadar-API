"""SportRadar Tennis v3 -> relational warehouse (SQLite / MySQL / PostgreSQL).
Usage:  export SPORTRADAR_API_KEY=xxxx ; export DB_URL=mysql+pymysql://user:pass@host/db   (default sqlite:///tennis.db)
        python etl.py [--only competitions complexes rankings]
"""
import argparse, logging, os, time
import pandas as pd, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import (Column, ForeignKey, Index, Integer, MetaData, String, Table, CHAR, create_engine, delete)

log = logging.getLogger("etl")
BASE = os.getenv("SR_BASE", "https://api.sportradar.com/tennis/trial/v3/en")
ENDPOINTS = {"competitions": "competitions.json", "complexes": "complexes.json", "rankings": "double_competitor_rankings.json"}
PAUSE = float(os.getenv("SR_PAUSE", "1.2"))  # trial keys allow ~1 request/second

# ───────────── schema (dialect-agnostic; mirrors schema.sql) ─────────────
md = MetaData()
categories = Table("categories", md, Column("category_id", String(50), primary_key=True), Column("category_name", String(100), nullable=False))
competitions = Table("competitions", md, Column("competition_id", String(50), primary_key=True), Column("competition_name", String(100), nullable=False),
    Column("parent_id", String(50)), Column("type", String(20), nullable=False), Column("gender", String(10), nullable=False),
    Column("category_id", String(50), ForeignKey("categories.category_id")), Index("ix_comp_category", "category_id"), Index("ix_comp_parent", "parent_id"))
complexes = Table("complexes", md, Column("complex_id", String(50), primary_key=True), Column("complex_name", String(100), nullable=False))
venues = Table("venues", md, Column("venue_id", String(50), primary_key=True), Column("venue_name", String(100), nullable=False),
    Column("city_name", String(100), nullable=False), Column("country_name", String(100), nullable=False), Column("country_code", CHAR(3), nullable=False),
    Column("timezone", String(100), nullable=False), Column("complex_id", String(50), ForeignKey("complexes.complex_id")),
    Index("ix_venue_country", "country_name"), Index("ix_venue_complex", "complex_id"))
competitors = Table("competitors", md, Column("competitor_id", String(50), primary_key=True), Column("name", String(100), nullable=False),
    Column("country", String(100), nullable=False), Column("country_code", CHAR(3), nullable=False), Column("abbreviation", String(10), nullable=False),
    Index("ix_competitor_country", "country"))
rankings = Table("competitor_rankings", md, Column("rank_id", Integer, primary_key=True, autoincrement=True), Column("rank", Integer, nullable=False),
    Column("movement", Integer, nullable=False), Column("points", Integer, nullable=False), Column("competitions_played", Integer, nullable=False),
    Column("competitor_id", String(50), ForeignKey("competitors.competitor_id"), nullable=False), Column("ranking_name", String(50)),
    Column("gender", String(10)), Column("year", Integer), Column("week", Integer), Index("ix_rank_competitor", "competitor_id"), Index("ix_rank_period", "year", "week"))


# ───────────── extract ─────────────
def make_session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], respect_retry_after_header=True)))
    return s


def fetch(session, name):
    key = os.getenv("SPORTRADAR_API_KEY")
    if not key: raise SystemExit("Set SPORTRADAR_API_KEY")
    try:
        r = session.get(f"{BASE}/{ENDPOINTS[name]}", params={"api_key": key}, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        log.error("API call failed for %s: %s", name, e); raise
    finally:
        time.sleep(PAUSE)


# ───────────── transform (nested JSON -> flat frames) ─────────────
def tf_competitions(js):
    rows = [dict(competition_id=c["id"], competition_name=c.get("name"), parent_id=c.get("parent_id"), type=c.get("type") or "unknown",
                 gender=c.get("gender") or "unknown", category_id=(c.get("category") or {}).get("id"),
                 _cat_name=(c.get("category") or {}).get("name")) for c in js.get("competitions", [])]
    df = pd.DataFrame(rows).drop_duplicates("competition_id")
    cats = (df[["category_id", "_cat_name"]].dropna(subset=["category_id"]).drop_duplicates("category_id")
            .rename(columns={"_cat_name": "category_name"}).fillna({"category_name": "Unknown"}))
    return cats, df.drop(columns="_cat_name")


def tf_complexes(js):
    cx, vn = [], []
    for c in js.get("complexes", []):
        cx.append(dict(complex_id=c["id"], complex_name=c.get("name")))
        for v in c.get("venues", []) or []:
            vn.append(dict(venue_id=v["id"], venue_name=v.get("name"), city_name=v.get("city_name") or "Unknown", country_name=v.get("country_name") or "Unknown",
                           country_code=(v.get("country_code") or "UNK")[:3], timezone=v.get("timezone") or "UTC", complex_id=c["id"]))
    return pd.DataFrame(cx).drop_duplicates("complex_id"), pd.DataFrame(vn).drop_duplicates("venue_id")


def tf_rankings(js):
    comp, rk = {}, []
    for board in js.get("rankings", []):
        for r in board.get("competitor_rankings", []):
            c = r["competitor"]
            comp[c["id"]] = dict(competitor_id=c["id"], name=c.get("name"), country=c.get("country") or "Unknown",
                                 country_code=(c.get("country_code") or "UNK")[:3], abbreviation=(c.get("abbreviation") or "")[:10])
            rk.append(dict(rank=r.get("rank"), movement=r.get("movement") or 0, points=r.get("points") or 0, competitions_played=r.get("competitions_played") or 0,
                           competitor_id=c["id"], ranking_name=board.get("name"), gender=board.get("gender"), year=board.get("year"), week=board.get("week")))
    return pd.DataFrame(comp.values()), pd.DataFrame(rk)


# ───────────── load ─────────────
def load(engine, only):
    md.create_all(engine)
    s = make_session()
    with engine.begin() as cn:  # one transaction per run -> all-or-nothing
        if "competitions" in only:
            cats, comp = tf_competitions(fetch(s, "competitions"))
            cn.execute(delete(competitions)); cn.execute(delete(categories))
            cats.to_sql("categories", cn, if_exists="append", index=False); comp.to_sql("competitions", cn, if_exists="append", index=False)
            log.info("categories=%d competitions=%d", len(cats), len(comp))
        if "complexes" in only:
            cx, vn = tf_complexes(fetch(s, "complexes"))
            cn.execute(delete(venues)); cn.execute(delete(complexes))
            cx.to_sql("complexes", cn, if_exists="append", index=False); vn.to_sql("venues", cn, if_exists="append", index=False)
            log.info("complexes=%d venues=%d", len(cx), len(vn))
        if "rankings" in only:
            cp, rk = tf_rankings(fetch(s, "rankings"))
            for (n, y, w) in rk[["ranking_name", "year", "week"]].drop_duplicates().itertuples(index=False):  # idempotent weekly reload
                cn.execute(delete(rankings).where(rankings.c.ranking_name == n, rankings.c.year == int(y), rankings.c.week == int(w)))
            existing = set(pd.read_sql("SELECT competitor_id FROM competitors", cn).competitor_id)
            cp[~cp.competitor_id.isin(existing)].to_sql("competitors", cn, if_exists="append", index=False)
            rk.to_sql("competitor_rankings", cn, if_exists="append", index=False)
            log.info("competitors=%d ranking rows=%d", len(cp), len(rk))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--only", nargs="+", default=list(ENDPOINTS), choices=list(ENDPOINTS))
    load(create_engine(os.getenv("DB_URL", "sqlite:///tennis.db"), future=True), ap.parse_args().only)
