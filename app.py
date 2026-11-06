"""🎾 Tennis Intelligence 360 — recruiter-ready Streamlit app on the SportRadar SQL warehouse.
Author : P Suman Sangeet · PGDM (Big Data Analytics) · Data Science & AI
         Ritika Tripathi
         Prakhar Singh
         Abhay Kumar Vishwakarma
Run    : pip install streamlit pandas numpy plotly sqlalchemy pymysql scikit-learn python-docx matplotlib && streamlit run app.py
DB     : st.secrets["DB_URL"]  |  env DB_URL  |  default sqlite:///tennis.db
Deploy : Streamlit Community Cloud -> New app -> app.py -> Secrets: DB_URL = "mysql+pymysql://user:pass@host/db"
"""
import os, re, time
import numpy as np, pandas as pd
import plotly.express as px, plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, inspect, text

# ───────────────────────── profile (edit once) ─────────────────────────
AUTHOR = "P Suman Sangeet, Ritika Tripathi, Prakhar Singh, Abhay Kumar Vishwakarma"
ROLE = "INNOVEXIS Data Science & Gen AI · PGDM Big Data Analytics"
LINKS = {"GitHub": "https://github.com/SUMANSANGEET", "LinkedIn": "www.linkedin.com/in/p-suman-sangeet"}  # blank = hidden

st.set_page_config(page_title="Tennis Intelligence 360", page_icon="🎾", layout="wide")
SEQ = ["#0F766E", "#2563EB", "#F59E0B", "#DB2777", "#7C3AED", "#16A34A", "#EA580C", "#0891B2"]
px.defaults.template, px.defaults.color_discrete_sequence = "plotly_white", SEQ
st.markdown("""<style>
.block-container{padding-top:1.4rem}
.hero{background:linear-gradient(120deg,#0F766E,#2563EB);color:#fff;padding:20px 26px;border-radius:14px;margin-bottom:14px}
.hero h1{margin:0;font-size:1.9rem;color:#fff}.hero p{margin:4px 0 0;opacity:.9}
.kpi{background:#F8FAFC;border:1px solid #E2E8F0;border-left:5px solid var(--c);border-radius:10px;padding:12px 16px}
.kpi b{display:block;font-size:1.65rem;color:#0F172A}.kpi span{font-size:.72rem;color:#64748B;text-transform:uppercase;letter-spacing:.04em}
.kpi i{display:block;font-size:.78rem;color:#64748B;font-style:normal}
.brand-lockup{display:flex;align-items:center;gap:11px;margin:2px 0 18px}
.brand-mark{width:48px;height:48px;flex:0 0 48px;filter:drop-shadow(0 5px 10px rgba(15,118,110,.18))}
.brand-name{font-size:1.02rem;font-weight:800;letter-spacing:.01em;line-height:1.15}
.brand-tag{font-size:.66rem;color:#64748B;letter-spacing:.13em;text-transform:uppercase;margin-top:4px}
.hero-brand{display:flex;align-items:center;gap:14px}
.hero-brand .brand-mark{width:56px;height:56px;flex-basis:56px;filter:none}
.flow{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin:6px 0 4px}
.step{flex:1 1 150px;background:#fff;border:1px solid #E2E8F0;border-top:4px solid var(--c);border-radius:10px;padding:10px 12px}
.step b{display:block;font-size:.9rem;color:#0F172A}.step span{font-size:.75rem;color:#64748B}
.arrow{align-self:center;color:#94A3B8;font-size:1.3rem}
.chip{display:inline-block;background:#ECFDF5;color:#0F766E;border:1px solid #A7F3D0;border-radius:999px;padding:3px 11px;margin:3px 4px 3px 0;font-size:.78rem;font-weight:600}
.insight{background:#F0F9FF;border-left:4px solid #2563EB;border-radius:8px;padding:9px 14px;margin:6px 0;color:#0F172A}
.foot{color:#64748B;font-size:.75rem;text-align:center;margin-top:28px}
</style>""", unsafe_allow_html=True)


# ───────────────────────── database layer ─────────────────────────
def _db_url():
    try:
        return st.secrets["DB_URL"]
    except Exception:
        return os.getenv("DB_URL", "sqlite:///tennis.db")


@st.cache_resource
def get_engine(url):
    return create_engine(url, pool_pre_ping=True, future=True)


ENG = get_engine(_db_url())
RK = '"rank"' if ENG.dialect.name == "postgresql" else "`rank`"


@st.cache_data(ttl=60, show_spinner=False)
def q(sql, params=None):
    """Live, parameterised query execution (cached 60 s so the app stays snappy)."""
    with ENG.connect() as c:
        return pd.read_sql(text(sql), c, params=params or {})


def safe_select(sql):
    s = sql.strip().rstrip(";")
    return (s.lower().startswith(("select", "with")) and ";" not in s and
            not re.search(r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|pragma|grant)\b", s, re.I))


try:
    RANKS = q(f"""SELECT r.{RK} AS rnk, r.movement, r.points, r.competitions_played AS events, r.ranking_name,
        r.gender AS board_gender, r.year, r.week, c.competitor_id, c.name, c.country, c.country_code
        FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id""")
    COMP = q("""SELECT c.competition_id, c.competition_name, c.parent_id, LOWER(c.type) AS type, LOWER(c.gender) AS gender,
        COALESCE(NULLIF(k.category_name,''),'Uncategorised') AS category
        FROM competitions c LEFT JOIN categories k ON k.category_id = c.category_id""")
    VEN = q("""SELECT v.venue_id, v.venue_name, v.city_name, v.country_name, v.country_code, v.timezone,
        COALESCE(x.complex_name,'—') AS complex_name FROM venues v LEFT JOIN complexes x ON x.complex_id = v.complex_id""")
except Exception as e:
    st.error(f"Cannot read the database ({_db_url().split('@')[-1]}). Run the ETL notebook first or set DB_URL.\n\n{e}")
    st.stop()

RANKS["board"] = RANKS.ranking_name.where(RANKS.ranking_name.fillna("Unknown").ne("Unknown"), RANKS.board_gender.fillna("").str.title())
RANKS["period"] = RANKS.year.astype(int).astype(str) + " · wk " + RANKS.week.astype(int).astype(str).str.zfill(2)

# ───────────────────────── brand identity ─────────────────────────
LOGO_SVG = """
<svg class="brand-mark" viewBox="0 0 100 100" role="img" aria-label="Tennis Intelligence 360 logo" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="courtGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#14B8A6"/><stop offset="100%" stop-color="#2563EB"/></linearGradient></defs>
  <rect x="3" y="3" width="94" height="94" rx="27" fill="url(#courtGradient)"/>
  <circle cx="50" cy="50" r="29" fill="#D9F99D" stroke="#FFFFFF" stroke-width="3"/>
  <path d="M31 25 C48 38 48 62 31 75 M69 25 C52 38 52 62 69 75" fill="none" stroke="#0F766E" stroke-width="4.2" stroke-linecap="round"/>
  <path d="M13 50 H25 M75 50 H87" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" opacity=".8"/>
  <circle cx="78" cy="22" r="5" fill="#FBBF24" stroke="#FFFFFF" stroke-width="2"/>
</svg>"""


def brand_lockup():
    st.markdown(f'<div class="brand-lockup">{LOGO_SVG}<div><div class="brand-name">TENNIS INTELLIGENCE 360</div>'
                '<div class="brand-tag">Performance • Data • Insights</div></div></div>', unsafe_allow_html=True)


# ───────────────────────── sidebar ─────────────────────────
PG = {"show": "⭐ Recruiter Showcase", "dash": "🏠 Dashboard", "glob": "🌐 Global Explorer", "search": "🔎 Search & Filter",
      "profile": "👤 Competitor Profile", "country": "🌍 Country Analysis", "lead": "🏆 Leaderboards", "adv": "🧠 Advanced Analytics",
      "ml": "🤖 ML Intelligence", "comp": "🎪 Competitions", "ven": "🏟️ Venues", "dq": "✅ Data Quality",
      "report": "📘 Project Report", "sql": "🧪 SQL Lab"}
PAGES = list(PG.values())
with st.sidebar:
    brand_lockup()
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.divider()
periods = sorted(RANKS.period.unique(), reverse=True)
period = st.sidebar.selectbox("Ranking snapshot", periods)
snap_all = RANKS[RANKS.period == period]
boards = ["All boards"] + sorted(snap_all.board.dropna().unique())
board = st.sidebar.selectbox("Ranking board", boards)
S = snap_all if board == "All boards" else snap_all[snap_all.board == board]
st.sidebar.caption(f"DB: {ENG.dialect.name} · {len(S):,} ranking rows in view")
if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear(); st.rerun()
st.sidebar.divider()
st.sidebar.markdown(f"**{AUTHOR}**  \n{ROLE}")
for k, v in LINKS.items():
    if v: st.sidebar.markdown(f"[{k}]({v})")


# ───────────────────────── helpers ─────────────────────────
def hero(title, sub):
    st.markdown(f'<div class="hero"><div class="hero-brand">{LOGO_SVG}<div><h1>{title}</h1><p>{sub}</p></div></div></div>',
                unsafe_allow_html=True)


def kpis(items):
    for col, (label, val, sub, c) in zip(st.columns(len(items)), items):
        col.markdown(f'<div class="kpi" style="--c:{c}"><span>{label}</span><b>{val}</b><i>{sub}</i></div>', unsafe_allow_html=True)


def empty(df):
    if df.empty:
        st.warning("No data matches the current filters."); return True
    return False


def table(df, **kw):
    st.dataframe(df, width="stretch", hide_index=True, **kw)


def chart(fig, **kw):
    st.plotly_chart(fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), font=dict(size=12)), width="stretch", **kw)


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return 0.0 if n == 0 or x.sum() == 0 else float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def insights(df):
    """Auto-generated, data-driven headline findings (re-computed for the current filters)."""
    out = []
    if len(df):
        t10 = df.nlargest(10, "points").points.sum() / df.points.sum() * 100
        out.append(f"🏆 The top 10 players hold **{t10:.1f}%** of all ranking points — points inequality (Gini) is **{gini(df.points):.2f}**.")
        vc = df.country.value_counts()
        out.append(f"🌍 **{vc.index[0]}** has the deepest pool with **{vc.iloc[0]}** ranked players; **{df.country.nunique()}** nations are represented.")
        e = df[df.events >= 5].assign(eff=lambda d: d.points / d.events)
        if len(e):
            b = e.loc[e.eff.idxmax()]
            out.append(f"⚡ Most efficient (≥5 events): **{b['name']}** ({b.country}) with **{b.eff:,.0f}** points per event.")
        c = df.loc[df.movement.idxmax()]
        out.append(f"🚀 Biggest climber: **{c['name']}** (**{int(c.movement):+d}** places vs previous week).")
    if len(COMP):
        out.append(f"🎪 Doubles events are **{(COMP.type == 'doubles').mean() * 100:.1f}%** and women's events "
                   f"**{(COMP.gender == 'women').mean() * 100:.1f}%** of **{len(COMP):,}** competitions across {COMP.category.nunique()} categories.")
    out.append(f"🏟️ **{len(VEN):,}** venues in **{VEN.country_name.nunique()}** countries covering **{VEN.timezone.nunique()}** timezones.")
    return out


PTS_CFG = {"points": st.column_config.ProgressColumn("Points", format="%d", min_value=0, max_value=int(max(S.points.max(), 1)) if len(S) else 1),
           "movement": st.column_config.NumberColumn("Move", format="%+d")}
SHOW = {"rnk": "Rank", "name": "Competitor", "country": "Country", "points": "points", "movement": "movement", "events": "Events", "board": "Board"}


def view(df):
    return df[list(SHOW)].rename(columns=SHOW)


# ───────────────────────── project report (data-driven documentation) ─────────────────────────
TABLES = ["categories", "competitions", "complexes", "venues", "competitors", "competitor_rankings"]
DQ_CHECKS = {
    "Competitions with unknown category": "SELECT COUNT(*) AS n FROM competitions c LEFT JOIN categories k ON k.category_id=c.category_id WHERE c.category_id IS NOT NULL AND k.category_id IS NULL",
    "Competitions with missing parent record": "SELECT COUNT(*) AS n FROM competitions c LEFT JOIN competitions p ON p.competition_id=c.parent_id WHERE c.parent_id IS NOT NULL AND p.competition_id IS NULL",
    "Venues with unknown complex": "SELECT COUNT(*) AS n FROM venues v LEFT JOIN complexes x ON x.complex_id=v.complex_id WHERE v.complex_id IS NOT NULL AND x.complex_id IS NULL",
    "Rankings without competitor": "SELECT COUNT(*) AS n FROM competitor_rankings r LEFT JOIN competitors c ON c.competitor_id=r.competitor_id WHERE c.competitor_id IS NULL",
    "Duplicate competitor IDs": "SELECT COUNT(*) AS n FROM (SELECT competitor_id FROM competitors GROUP BY competitor_id HAVING COUNT(*)>1) d",
    "Duplicate venue IDs": "SELECT COUNT(*) AS n FROM (SELECT venue_id FROM venues GROUP BY venue_id HAVING COUNT(*)>1) d",
    "Negative points": "SELECT COUNT(*) AS n FROM competitor_rankings WHERE points < 0",
    "Venues missing timezone": "SELECT COUNT(*) AS n FROM venues WHERE timezone IS NULL OR timezone = ''",
}
GC = {"mysql": "GROUP_CONCAT(venue_name SEPARATOR '; ')", "postgresql": "STRING_AGG(venue_name, '; ')"}.get(ENG.dialect.name, "GROUP_CONCAT(venue_name, '; ')")
_J = f"competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id"
_LATEST = "r.year = (SELECT MAX(year) FROM competitor_rankings) AND r.week = (SELECT MAX(week) FROM competitor_rankings WHERE year = (SELECT MAX(year) FROM competitor_rankings))"
# (group, id, title, business question, SQL, default parameters)
QCAT = [
    ("A · Competitions", "A1", "Competitions with category", "List all competitions along with their category name",
     "SELECT c.competition_id, c.competition_name, k.category_name FROM competitions c LEFT JOIN categories k ON k.category_id = c.category_id ORDER BY k.category_name, c.competition_name", {}),
    ("A · Competitions", "A2", "Competitions per category", "Count the number of competitions in each category",
     "SELECT k.category_name, COUNT(*) AS competitions FROM competitions c JOIN categories k ON k.category_id = c.category_id GROUP BY k.category_name ORDER BY competitions DESC", {}),
    ("A · Competitions", "A3", "Doubles competitions", "Find all competitions of type 'doubles'",
     "SELECT competition_id, competition_name, gender FROM competitions WHERE type = 'doubles' ORDER BY competition_name", {}),
    ("A · Competitions", "A4", "Competitions in a category", "Get competitions that belong to a specific category (e.g. ITF Men)",
     "SELECT c.competition_name, c.type, c.gender FROM competitions c JOIN categories k ON k.category_id = c.category_id WHERE k.category_name = :category ORDER BY c.competition_name", {"category": "ITF Men"}),
    ("A · Competitions", "A5", "Parents and sub-competitions", "Identify parent competitions and their sub-competitions",
     "SELECT p.competition_name AS parent, s.competition_name AS sub_competition FROM competitions s JOIN competitions p ON p.competition_id = s.parent_id ORDER BY parent, sub_competition", {}),
    ("A · Competitions", "A6", "Type mix by category", "Analyse the distribution of competition types by category",
     "SELECT k.category_name, c.type, COUNT(*) AS n FROM competitions c JOIN categories k ON k.category_id = c.category_id GROUP BY k.category_name, c.type ORDER BY k.category_name, n DESC", {}),
    ("A · Competitions", "A7", "Top-level competitions", "List all competitions with no parent",
     "SELECT competition_id, competition_name, type, gender FROM competitions WHERE parent_id IS NULL ORDER BY competition_name", {}),
    ("B · Venues", "B1", "Venues with complex", "List all venues along with their associated complex name",
     "SELECT v.venue_name, v.city_name, x.complex_name FROM venues v LEFT JOIN complexes x ON x.complex_id = v.complex_id ORDER BY x.complex_name", {}),
    ("B · Venues", "B2", "Venues per complex", "Count the number of venues in each complex",
     "SELECT x.complex_name, COUNT(v.venue_id) AS venues FROM complexes x LEFT JOIN venues v ON v.complex_id = x.complex_id GROUP BY x.complex_id, x.complex_name ORDER BY venues DESC", {}),
    ("B · Venues", "B3", "Venues in a country", "Get details of venues in a specific country (e.g. Chile)",
     "SELECT venue_name, city_name, timezone FROM venues WHERE country_name = :country ORDER BY city_name", {"country": "Chile"}),
    ("B · Venues", "B4", "Venues and timezones", "Identify all venues and their timezones",
     "SELECT venue_name, timezone FROM venues ORDER BY timezone, venue_name", {}),
    ("B · Venues", "B5", "Multi-venue complexes", "Find complexes that have more than one venue",
     "SELECT x.complex_name, COUNT(v.venue_id) AS venues FROM complexes x JOIN venues v ON v.complex_id = x.complex_id GROUP BY x.complex_id, x.complex_name HAVING COUNT(v.venue_id) > 1 ORDER BY venues DESC", {}),
    ("B · Venues", "B6", "Venues grouped by country", "List venues grouped by country",
     f"SELECT country_name, COUNT(*) AS venues, {GC} AS venue_list FROM venues GROUP BY country_name ORDER BY venues DESC", {}),
    ("B · Venues", "B7", "Venues of a complex", "Find all venues for a specific complex (e.g. Nacional)",
     "SELECT v.venue_name, v.city_name, v.country_name FROM venues v JOIN complexes x ON x.complex_id = v.complex_id WHERE x.complex_name = :complex ORDER BY v.venue_name", {"complex": "Nacional"}),
    ("C · Rankings", "C1", "Competitors with rank and points", "Get all competitors with their rank and points",
     f"SELECT c.name, r.{RK} AS rnk, r.points FROM {_J} ORDER BY r.{RK}", {}),
    ("C · Rankings", "C2", "Top 5", "Find competitors ranked in the top 5",
     f"SELECT c.name, r.{RK} AS rnk, r.points FROM {_J} WHERE r.{RK} <= 5 ORDER BY r.{RK}", {}),
    ("C · Rankings", "C3", "Stable rank", "List competitors with no rank movement",
     f"SELECT c.name, r.{RK} AS rnk FROM {_J} WHERE r.movement = 0 ORDER BY r.{RK}", {}),
    ("C · Rankings", "C4", "Points of a country", "Total points of competitors from a specific country (e.g. Croatia)",
     f"SELECT c.country, COUNT(*) AS competitors, SUM(r.points) AS total_points FROM {_J} WHERE c.country = :country GROUP BY c.country", {"country": "Croatia"}),
    ("C · Rankings", "C5", "Competitors per country", "Count the number of competitors per country",
     "SELECT country, COUNT(*) AS competitors FROM competitors GROUP BY country ORDER BY competitors DESC", {}),
    ("C · Rankings", "C6", "Highest points this week", "Find competitors with the highest points in the current week",
     f"SELECT c.name, c.country, r.points FROM {_J} WHERE {_LATEST} ORDER BY r.points DESC LIMIT 10", {}),
]
EVAL = [("Data extraction accuracy", "etl.py: typed flatteners, defaults for missing fields, de-duplication on keys", "Data Quality tab · completeness"),
        ("SQL database design", "6 normalised tables, PK/FK, self-reference for hierarchy", "Data & pipeline tab · ERD + live data dictionary"),
        ("Query efficiency", "Indexes on every FK, country, period; timed execution of all 20 queries", "SQL catalogue tab · Run all"),
        ("Streamlit functionality", f"{len(PAGES)} interactive pages, filters, CSV export, live SQL", "Sidebar navigation"),
        ("Project completeness", "API → SQL → analysis → app → docs", "Objectives tab · deliverables"),
        ("Documentation quality", "This report + README.md + sql_queries.sql", "Export tab"),
        ("Presentation & usability", "Recruiter showcase, KPI cards, consistent palette", "Recruiter Showcase page"),
        ("Error handling", "Retries/back-off, transactions, SELECT-only guard, empty-state handling", "Challenges tab"),
        ("Innovation & creativity", "Gini/Lorenz inequality, player tiers, efficiency quadrant, live data-health score", "Advanced Analytics page")]


def dq_results():
    res = []
    for k, sql in DQ_CHECKS.items():
        try: n = int(q(sql).n[0]); res.append((k, n, "✅ Pass" if n == 0 else "⚠️ Review"))
        except Exception as e: res.append((k, -1, f"❌ {str(e)[:40]}"))
    return pd.DataFrame(res, columns=["check", "violations", "status"])


def table_counts():
    return pd.DataFrame({"table": TABLES, "rows": [int(q(f"SELECT COUNT(*) AS n FROM {t}").n[0]) for t in TABLES]})


def data_dictionary():
    insp = inspect(ENG); rows = []
    for t in TABLES:
        pk = set(insp.get_pk_constraint(t).get("constrained_columns") or [])
        fk = {c: f"{f['referred_table']}.{f['referred_columns'][0]}" for f in insp.get_foreign_keys(t) for c in f["constrained_columns"]}
        for c in insp.get_columns(t):
            rows.append((t, c["name"], str(c["type"]), "NO" if not c["nullable"] else "YES", "PK" if c["name"] in pk else (f"FK → {fk[c['name']]}" if c["name"] in fk else "")))
    return pd.DataFrame(rows, columns=["table", "column", "type", "nullable", "key"])


def run_timed(sql, params):
    t0 = time.perf_counter()
    with ENG.connect() as c: df = pd.read_sql(text(sql), c, params=params)
    return df, (time.perf_counter() - t0) * 1000


def auto_chart(R, key):
    num = R.select_dtypes("number").columns.tolist(); cat = [c for c in R.columns if c not in num]
    if len(R) < 2 or not num or not cat or R[cat[0]].nunique() < 2: return
    grp = cat[1] if len(cat) > 1 and R[cat[1]].nunique() <= 8 else None
    kw = dict(color=grp) if grp else dict(color=num[-1], color_continuous_scale="Teal")
    fig = px.bar(R.head(25), x=num[-1], y=cat[0], orientation="h", **kw)
    chart(fig.update_yaxes(autorange="reversed"), key=key)


def recommendations(L):
    out = []
    cc = COMP.category.value_counts()
    out.append(f"**Resource allocation** — {', '.join(cc.index[:3])} hold {cc.iloc[:3].sum() / len(COMP) * 100:.0f}% of all {len(COMP):,} competitions: prioritise scheduling, officiating and broadcast capacity there first.")
    pl = L.country.value_counts()
    out.append(f"**Talent pipeline** — {', '.join(pl.index[:3])} supply {pl.iloc[:3].sum() / len(L) * 100:.0f}% of ranked doubles players: focus development partnerships and scouting where depth already exists, and study under-represented nations for growth.")
    vc = VEN.country_name.value_counts()
    multi = (VEN[VEN.complex_name != "—"].groupby("complex_name").size() > 1).sum()
    out.append(f"**Venue footprint** — {', '.join(vc.index[:3])} lead with {vc.iloc[:3].sum() / len(VEN) * 100:.0f}% of {len(VEN):,} venues; {multi} complexes host several venues and are natural hubs for multi-event weeks.")
    out.append(f"**Competitive balance** — points Gini is {gini(L.points):.2f} and the top-10 hold {L.nlargest(10, 'points').points.sum() / L.points.sum() * 100:.1f}% of points: monitor concentration weekly to spot an opening or closing elite gap.")
    out.append("**Data operations** — schedule `etl.py` weekly (cron / GitHub Actions) so rank-history charts, mover analysis and trend detection become available.")
    return out


def build_report_md(L, cnt, dq):
    md = [f"# Tennis Intelligence 360 — Project Report\n_{AUTHOR} · {ROLE} · snapshot {L.period.iloc[0]}_\n",
          "## 1. Executive summary", *[f"- {i}" for i in insights(L)],
          "\n## 2. Pipeline", "SportRadar Tennis API v3 → `etl.py` (retry, flatten, transactional load) → SQL warehouse (6 tables, PK/FK, indexes) → 20 SQL queries → Streamlit app.",
          "\n## 3. Row counts", cnt.to_markdown(index=False) if hasattr(cnt, "to_markdown") and _has_tabulate() else cnt.to_string(index=False),
          f"\n## 4. Data quality — score {(dq.status == '✅ Pass').mean() * 100:.0f}%", dq.to_string(index=False),
          "\n## 5. Recommendations", *[f"- {r}" for r in recommendations(L)],
          "\n## 6. SQL catalogue", *[f"- **{i}** {t}: {b}" for _, i, t, b, _, _ in QCAT]]
    return "\n".join(md)


def _has_tabulate():
    try: import tabulate; return True
    except Exception: return False


def report_page():
    hero("Project Report", "Detailed documentation — objectives, pipeline, schema, profiling, findings, SQL catalogue, challenges and recommendations")
    L = RANKS[RANKS.period == RANKS.period.max()]
    cnt, dq = table_counts(), dq_results()
    score = (dq.status == "✅ Pass").mean() * 100
    T = st.tabs(["1 · Executive summary", "2 · Objectives & scope", "3 · Data & pipeline", "4 · Data profiling", "5 · Findings",
                 "6 · SQL catalogue", "7 · Challenges", "8 · Recommendations", "9 · Export"])

    with T[0]:
        kpis([("Rows in warehouse", f"{cnt.rows.sum():,}", f"{len(TABLES)} tables", SEQ[0]), ("Competitions", f"{len(COMP):,}", f"{COMP.category.nunique()} categories", SEQ[1]),
              ("Venues", f"{len(VEN):,}", f"{VEN.country_name.nunique()} countries", SEQ[2]), ("Ranked competitors", f"{L.competitor_id.nunique():,}", f"{L.country.nunique()} nations", SEQ[3]),
              ("Data health", f"{score:.0f}%", f"{(dq.status == '✅ Pass').sum()}/{len(dq)} checks", "#16A34A" if score == 100 else "#F59E0B")])
        st.subheader("Key findings")
        for line in insights(L): st.markdown(f'<div class="insight">{line}</div>', unsafe_allow_html=True)
        st.subheader("Business use cases → evidence")
        table(pd.DataFrame([("Event exploration", "Navigate competition hierarchies, filter by type/gender/category", "Competitions page · Findings § Competitions"),
                            ("Trend analysis", "Distribution of events by type, gender and level", "Dashboard · Findings § Competitions"),
                            ("Performance insights", "Player participation, efficiency, tiers, inequality", "Advanced Analytics · Findings § Rankings"),
                            ("Decision support", "Data-driven allocation of resources", "Recommendations tab")], columns=["Use case", "What the app does", "Where to see it"]))

    with T[1]:
        st.markdown("**Problem statement.** Build a solution that extracts sports-competition data from the Sportradar Tennis API, stores it in a normalised relational database, "
                    "and lets users explore competition structures, venues and doubles rankings through an interactive application.")
        st.markdown("**Objectives**\n1. Automate API extraction and JSON → relational transformation.\n2. Design a normalised schema with keys and indexes.\n"
                    "3. Answer 20 business questions with SQL.\n4. Deliver an interactive Streamlit dashboard and full documentation.")
        st.subheader("Deliverables")
        table(pd.DataFrame([("SQL database", "schema.sql · 6 tables, PK/FK, indexes", "✅"), ("API scripts", "etl.py · retries, pacing, idempotent loads", "✅"),
                            ("Streamlit app", f"app.py · {len(PAGES)} pages", "✅"), ("Documentation", "README.md · sql_queries.sql · this report", "✅")], columns=["Deliverable", "Evidence", "Status"]))
        st.subheader("Evaluation criteria → where addressed")
        table(pd.DataFrame(EVAL, columns=["Criterion", "How it is met", "Where to verify"]))

    with T[2]:
        st.markdown('<div class="flow"><div class="step" style="--c:#0F766E"><b>Extract</b><span>requests session · back-off · Retry-After · 1.2 s pacing</span></div><div class="arrow">➜</div>'
                    '<div class="step" style="--c:#2563EB"><b>Transform</b><span>flatten nested JSON · defaults · de-duplicate on keys</span></div><div class="arrow">➜</div>'
                    '<div class="step" style="--c:#F59E0B"><b>Load</b><span>single transaction · FK-safe order · idempotent</span></div><div class="arrow">➜</div>'
                    '<div class="step" style="--c:#DB2777"><b>Analyse</b><span>20 SQL queries · timed</span></div><div class="arrow">➜</div>'
                    '<div class="step" style="--c:#7C3AED"><b>Serve</b><span>Streamlit · live DB · read-only guard</span></div></div>', unsafe_allow_html=True)
        st.subheader("Source endpoints")
        table(pd.DataFrame([("Competitions", "competitions.json", "categories, competitions"), ("Complexes", "complexes.json", "complexes, venues"),
                            ("Doubles competitor rankings", "double_competitor_rankings.json", "competitors, competitor_rankings")], columns=["Dataset", "Endpoint", "Tables loaded"]))
        st.subheader("Entity-relationship diagram")
        st.graphviz_chart("""digraph G { rankdir=LR; node [shape=record, style=filled, fillcolor="#F0FDFA", color="#0F766E", fontname="Helvetica"];
          categories [label="{categories|PK category_id|category_name}"];
          competitions [label="{competitions|PK competition_id|competition_name|parent_id (self)|type · gender|FK category_id}"];
          complexes [label="{complexes|PK complex_id|complex_name}"];
          venues [label="{venues|PK venue_id|venue_name · city_name|country_name · code|timezone|FK complex_id}"];
          competitors [label="{competitors|PK competitor_id|name · country|country_code|abbreviation}"];
          rankings [label="{competitor_rankings|PK rank_id|rank · movement · points|competitions_played|ranking_name · year · week|FK competitor_id}"];
          categories -> competitions [label="1:N"]; complexes -> venues [label="1:N"]; competitors -> rankings [label="1:N"]; competitions -> competitions [label="parent"]; }""")
        st.subheader("Live data dictionary (read from the database)")
        try:
            dd = data_dictionary(); tsel = st.multiselect("Tables", TABLES, default=TABLES[:2]); table(dd[dd.table.isin(tsel)] if tsel else dd)
        except Exception as e:
            st.info(f"Data dictionary unavailable on this connection: {e}")

    with T[3]:
        a, b = st.columns([1, 2])
        with a: table(cnt)
        with b: chart(px.bar(cnt.sort_values("rows"), x="rows", y="table", orientation="h", text="rows", log_x=True, title="Rows per table (log scale)"))
        st.subheader("Completeness (% non-null)")
        c1, c2, c3 = st.columns(3)
        for col, (name, df) in zip((c1, c2, c3), [("competitions", COMP), ("venues", VEN), ("rankings", L[["rnk", "movement", "points", "events", "name", "country", "country_code"]])]):
            comp = ((1 - df.isna().mean()) * 100).rename("pct").rename_axis("column").reset_index()
            with col: chart(px.bar(comp, x="pct", y="column", orientation="h", range_x=[0, 100], title=name, color_discrete_sequence=[SEQ[0]]), key=f"cmp_{name}")
        st.subheader(f"Integrity checks — health score {score:.0f}%")
        table(dq)

    with T[4]:
        sec = st.radio("Dataset", ["🎪 Competitions", "🏟️ Venues", "🏆 Doubles rankings"], horizontal=True)
        if sec.startswith("🎪"):
            cc = COMP.groupby("category").agg(n=("competition_id", "count"), doubles_pct=("type", lambda s: (s == "doubles").mean() * 100)).reset_index().nlargest(15, "n")
            a, b = st.columns(2)
            with a: chart(px.bar(cc, x="n", y="category", color="doubles_pct", orientation="h", color_continuous_scale="Teal", title="Competitions per category (colour = % doubles)").update_yaxes(autorange="reversed"))
            mix = COMP[COMP.category.isin(cc.category.head(10))].groupby(["category", "type"]).size().reset_index(name="n")
            with b: chart(px.bar(mix, x="n", y="category", color="type", orientation="h", title="Type mix, top-10 categories (100%)").update_layout(barmode="stack", barnorm="percent").update_yaxes(autorange="reversed"))
            c, d = st.columns(2)
            with c: chart(px.pie(COMP.gender.value_counts().rename_axis("gender").reset_index(name="n"), names="gender", values="n", hole=.5, title="Gender split"))
            top = COMP.category.value_counts().head(12).index
            with d: chart(px.sunburst(COMP[COMP.category.isin(top)].groupby(["category", "type", "gender"]).size().reset_index(name="n"), path=["category", "type", "gender"], values="n", title="Hierarchy: category → type → gender"))
            par = COMP.parent_id.value_counts()
            st.markdown(f"**Reading the data.** {len(COMP):,} competitions fall into {COMP.category.nunique()} categories; **{cc.iloc[0].category}** is the largest ({int(cc.iloc[0].n):,}). "
                        f"{COMP.parent_id.isna().mean() * 100:.1f}% are top-level; the largest parent has **{int(par.iloc[0]) if len(par) else 0}** sub-competitions. "
                        f"Doubles make up {(COMP.type == 'doubles').mean() * 100:.1f}% and women's events {(COMP.gender == 'women').mean() * 100:.1f}% of the catalogue.")
        elif sec.startswith("🏟️"):
            vc = VEN.groupby(["country_name", "country_code"]).size().reset_index(name="venues")
            a, b = st.columns(2)
            with a: chart(px.choropleth(vc, locations="country_code", color="venues", hover_name="country_name", color_continuous_scale="YlGnBu", title="Venues by country"))
            with b: chart(px.bar(vc.nlargest(15, "venues"), x="venues", y="country_name", orientation="h", title="Top 15 countries").update_yaxes(autorange="reversed"))
            cx = VEN[VEN.complex_name != "—"].groupby("complex_name").size().rename("venues").reset_index()
            c, d = st.columns(2)
            with c: chart(px.histogram(cx, x="venues", title="Venues per complex"))
            tz = VEN.timezone.value_counts().head(15).rename_axis("timezone").reset_index(name="venues")
            with d: chart(px.bar(tz, x="venues", y="timezone", orientation="h", title="Top 15 timezones").update_yaxes(autorange="reversed"))
            st.markdown(f"**Reading the data.** {len(VEN):,} venues across {VEN.country_name.nunique()} countries and {VEN.timezone.nunique()} timezones; "
                        f"**{vc.nlargest(1, 'venues').country_name.iloc[0]}** has the most venues. {(cx.venues > 1).sum()} of {len(cx):,} complexes host more than one venue (largest: {int(cx.venues.max()) if len(cx) else 0}).")
        else:
            D = L.assign(eff=L.points / L.events.clip(lower=1))
            a, b = st.columns(2)
            with a: chart(px.scatter(D, x="rnk", y="points", log_y=True, color="movement", color_continuous_scale="RdYlGn", color_continuous_midpoint=0, hover_name="name", hover_data=["country"], title="Rank vs points (log scale)"))
            cs = D.groupby("country").agg(players=("name", "count"), avg=("points", "mean")).reset_index().nlargest(12, "players")
            with b: chart(px.bar(cs, x="players", y="country", color="avg", color_continuous_scale="Teal", orientation="h", title="Depth by country (colour = avg points)").update_yaxes(autorange="reversed"))
            p = np.sort(D.points.values); cum = np.r_[0, np.cumsum(p) / max(p.sum(), 1)]; x = np.linspace(0, 1, len(cum))
            c, d = st.columns(2)
            with c: chart(go.Figure([go.Scatter(x=x, y=cum, fill="tozeroy", name="Lorenz", line_color=SEQ[0]), go.Scatter(x=[0, 1], y=[0, 1], name="Equality", line=dict(dash="dash", color="#94A3B8"))]).update_layout(title=f"Points inequality (Gini {gini(D.points):.2f})"))
            with d: chart(px.histogram(D, x="movement", nbins=40, title="Weekly rank movement", color_discrete_sequence=[SEQ[1]]))
            st.markdown(f"**Reading the data.** Snapshot {D.period.iloc[0]}: {len(D):,} ranking rows, {D.country.nunique()} nations. " + " ".join(i for i in insights(D)[:3]))

    with T[5]:
        st.caption("Every query from the brief, executable against the live database. Parameters are bound safely (no string concatenation).")
        grp = st.selectbox("Group", sorted({g for g, *_ in QCAT}))
        items = [x for x in QCAT if x[0] == grp]
        sel = st.selectbox("Query", [f"{i} · {t}" for _, i, t, *_ in items])
        _, qid, title, question, sql, defaults = next(x for x in items if f"{x[1]} · {x[2]}" == sel)
        st.markdown(f"**Business question:** {question}")
        params = {k: st.text_input(f"Parameter · {k}", v, key=f"qp_{qid}_{k}") for k, v in defaults.items()}
        st.code(sql, language="sql")
        try:
            R, ms = run_timed(sql, params)
            kpis([("Rows returned", f"{len(R):,}", "", SEQ[0]), ("Execution", f"{ms:,.1f} ms", "uncached", SEQ[1]), ("Columns", f"{len(R.columns)}", "", SEQ[2])])
            st.write(""); table(R.head(500)); auto_chart(R, f"qc_{qid}")
            st.download_button("⬇️ CSV", R.to_csv(index=False).encode(), f"{qid}.csv", "text/csv", key=f"dl_{qid}")
        except Exception as e:
            st.error(f"Query failed: {e}")
        st.divider()
        if st.button("⏱️ Run all 20 queries and benchmark"):
            log = []
            for g, i, t, bq, s, d in QCAT:
                try: r, m = run_timed(s, d); log.append((i, t, len(r), round(m, 1), "✅"))
                except Exception as e: log.append((i, t, -1, 0.0, f"❌ {str(e)[:30]}"))
            st.session_state["bench"] = pd.DataFrame(log, columns=["id", "query", "rows", "ms", "status"])
        if "bench" in st.session_state:
            B = st.session_state["bench"]
            kpis([("Queries OK", f"{(B.status == '✅').sum()}/{len(B)}", "", "#16A34A"), ("Total time", f"{B.ms.sum():,.0f} ms", "", SEQ[1]), ("Slowest", B.loc[B.ms.idxmax(), 'id'], f"{B.ms.max():,.1f} ms", SEQ[2])])
            st.write(""); chart(px.bar(B, x="id", y="ms", color="status", hover_data=["query", "rows"], title="Execution time per query (ms)")); table(B)

    with T[6]:
        table(pd.DataFrame([
            ("API rate limits (HTTP 429)", "Extraction stalls or is blocked", "Retry with exponential back-off, honour Retry-After, 1.2 s pacing", "etl.py · make_session / fetch"),
            ("Deeply nested JSON", "Brittle parsing, KeyErrors", "Per-endpoint flatteners with safe .get() defaults", "etl.py · tf_* functions"),
            ("Missing attributes vs NOT NULL", "Insert failures", "Explicit defaults (Unknown / UTC / 0)", "etl.py · transforms"),
            ("Reserved word `rank`", "SQL syntax errors across engines", "Dialect-aware quoting (backticks / double quotes)", "app.py · RK"),
            ("Re-running the pipeline", "Duplicate rows, broken history", "Idempotent delete-then-insert by key and ranking period", "etl.py · load"),
            ("Partial failures", "Half-loaded database", "One transaction per run (all-or-nothing)", "etl.py · engine.begin()"),
            ("Arbitrary SQL in the app", "Data loss / injection", "SELECT/WITH-only whitelist, single statement, bound parameters", "app.py · safe_select"),
            ("Slow repeated queries", "Laggy UI", "60 s cache, indexes on FKs and filter columns", "app.py · q · schema")],
            columns=["Challenge", "Risk", "Solution", "Where"]))
        st.subheader("Limitations")
        st.markdown("- Trial API quotas limit refresh frequency and history depth.\n- Rankings cover doubles competitors only; singles would require another endpoint.\n- Rank-history and trend charts need several weekly snapshots to become informative.")

    with T[7]:
        for r in recommendations(L): st.markdown(f'<div class="insight">{r}</div>', unsafe_allow_html=True)
        st.subheader("Future work")
        st.markdown("1. Weekly scheduled ETL (GitHub Actions / cron) to build a ranking time series.\n2. Singles rankings and match-level results for win-probability models.\n"
                    "3. Forecast rank movement and points (gradient boosting) with SHAP explanations.\n4. Pytest suite for transformers + CI pipeline.\n5. Role-based access and read-only DB user for production.")

    with T[8]:
        md = build_report_md(L, cnt, dq)
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download report (Markdown)", md, "tennis_project_report.md", "text/markdown")
        c2.download_button("⬇️ Download data dictionary (CSV)", data_dictionary().to_csv(index=False).encode(), "data_dictionary.csv", "text/csv")
        st.divider()
        st.markdown("**Word report (.docx)** — full report with charts, built from the live database.")
        if st.button("📄 Generate Word report"):
            try:
                from report_docx import build_docx
                with st.spinner("Building the Word report…"):
                    st.session_state["docx_bytes"] = build_docx(ENG, author=AUTHOR, role=ROLE, links=LINKS)
            except ImportError as e:
                st.error(f"Word export needs report_docx.py next to app.py and: pip install python-docx matplotlib ({e})")
            except Exception as e:
                st.error(f"Could not build the Word report: {e}")
        if "docx_bytes" in st.session_state:
            st.download_button("⬇️ Download Word report", st.session_state["docx_bytes"], "Tennis_Project_Report.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="dl_docx")
        st.caption("Tip: use your browser's Print → Save as PDF on this page for a PDF copy of the whole report.")
        with st.expander("Preview Markdown", expanded=True): st.markdown(md)


# ───────────────────────── pages ─────────────────────────
if page == PG["show"]:
    hero("Tennis Intelligence 360", f"End-to-end data project · SportRadar API → SQL warehouse → live analytics · by {AUTHOR}")
    if empty(S): st.stop()
    top = S.loc[S.points.idxmax()]
    kpis([("Competitors", f"{S.competitor_id.nunique():,}", f"{S.country.nunique()} countries", SEQ[0]),
          ("Competitions", f"{len(COMP):,}", f"{COMP.category.nunique()} categories", SEQ[1]),
          ("Venues", f"{len(VEN):,}", f"{VEN.country_name.nunique()} countries", SEQ[2]),
          ("Ranking rows", f"{len(RANKS):,}", f"{len(periods)} snapshot(s)", SEQ[3]),
          ("Top points", f"{int(top.points):,}", top["name"], SEQ[4])])
    st.subheader("How it works")
    st.markdown(
        '<div class="flow">'
        '<div class="step" style="--c:#0F766E"><b>1 · API ingestion</b><span>SportRadar Tennis v3: competitions, complexes, doubles rankings · retries &amp; rate-limit handling</span></div><div class="arrow">➜</div>'
        '<div class="step" style="--c:#2563EB"><b>2 · Transform</b><span>Nested JSON flattened into 3NF tables with typed keys</span></div><div class="arrow">➜</div>'
        '<div class="step" style="--c:#F59E0B"><b>3 · SQL warehouse</b><span>6 tables · PK/FK constraints · indexes · MySQL / PostgreSQL / SQLite</span></div><div class="arrow">➜</div>'
        '<div class="step" style="--c:#DB2777"><b>4 · Analytics</b><span>20 business SQL queries · Gini, tiers, efficiency</span></div><div class="arrow">➜</div>'
        '<div class="step" style="--c:#7C3AED"><b>5 · Streamlit app</b><span>Interactive, read-only SQL Lab, CSV export</span></div></div>', unsafe_allow_html=True)
    st.subheader("Headline insights")
    for line in insights(S):
        st.markdown(f'<div class="insight">{line}</div>', unsafe_allow_html=True)
    st.download_button("⬇️ Download insights (Markdown)", f"# Tennis Intelligence 360 — insights ({period})\n\n" + "\n".join(f"- {i}" for i in insights(S)),
                       "tennis_insights.md", "text/markdown")
    a, b = st.columns(2)
    with a:
        st.subheader("Skills demonstrated")
        st.markdown("".join(f'<span class="chip">{s}</span>' for s in
                    ["Python", "REST APIs", "ETL", "SQL (joins, CTEs, aggregates)", "Schema design", "MySQL / PostgreSQL", "Pandas", "NumPy",
                     "Plotly", "Streamlit", "Data quality checks", "Statistical analysis (Gini)", "Machine learning (scikit-learn)", "Anomaly detection", "Data storytelling"]), unsafe_allow_html=True)
    with b:
        st.subheader("Explore next")
        st.markdown("- **Advanced Analytics** — inequality curve, player tiers, efficiency quadrants\n"
                    "- **ML Intelligence** — player segmentation, rank estimator, anomaly detection\n"
                    "- **Data Quality** — live integrity checks on the warehouse\n- **SQL Lab** — run your own read-only queries")
    cc = S.groupby(["country", "country_code"]).agg(players=("name", "count"), points=("points", "sum")).reset_index()
    chart(px.choropleth(cc, locations="country_code", color="points", hover_name="country", hover_data=["players"],
                        color_continuous_scale="YlGnBu", title="Where the ranking points live"))

elif page == PG["dash"]:
    hero("Dashboard", f"Live analytics · snapshot {period}")
    if empty(S): st.stop()
    top = S.loc[S.points.idxmax()]
    kpis([("Total competitors", f"{S.competitor_id.nunique():,}", f"{S.board.nunique()} ranking board(s)", SEQ[0]),
          ("Countries represented", f"{S.country.nunique()}", "nationalities", SEQ[1]),
          ("Highest points", f"{int(top.points):,}", f"{top['name']} ({top.country})", SEQ[3]),
          ("Competitions", f"{len(COMP):,}", f"{COMP.category.nunique()} categories", SEQ[2]),
          ("Venues", f"{len(VEN):,}", f"{VEN.country_name.nunique()} countries", SEQ[4])])
    st.write("")
    a, b = st.columns(2)
    cc = S.groupby("country").agg(players=("name", "count"), avg=("points", "mean")).reset_index().nlargest(12, "players")
    with a: chart(px.bar(cc, x="players", y="country", orientation="h", color="avg", color_continuous_scale="Teal",
                         title="Top countries by ranked players (colour = avg points)").update_yaxes(autorange="reversed"))
    with b: chart(px.scatter(S, x="rnk", y="points", color="movement", size="events", size_max=16, hover_name="name",
                             hover_data=["country", "board"], color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                             title="Rank vs points (size = events, colour = movement)"))
    c, d = st.columns(2)
    mix = COMP.groupby(["category", "type"]).size().reset_index(name="n")
    mix = mix[mix.category.isin(COMP.category.value_counts().head(10).index)]
    with c: chart(px.bar(mix, x="n", y="category", color="type", orientation="h", title="Event mix in the 10 largest categories")
                  .update_yaxes(autorange="reversed"))
    mv = pd.concat([S.nlargest(6, "movement"), S.nsmallest(6, "movement")]).drop_duplicates("competitor_id").sort_values("movement")
    with d: chart(px.bar(mv, x="movement", y="name", orientation="h", color=np.where(mv.movement > 0, "Climber", "Faller"),
                         color_discrete_map={"Climber": "#16A34A", "Faller": "#DC2626"}, title="Biggest weekly movers"))
    for line in insights(S)[:2]:
        st.info(line)

elif page == PG["glob"]:
    hero("Global Explorer", "Cross-dataset view — one set of filters drives venues, players and competitions together")
    if empty(S): st.stop()
    countries_all = sorted(set(VEN.country_name.dropna().unique()) | set(S.country.dropna().unique()))
    g1, g2, g3 = st.columns([1.2, 1, 1.6])
    g_country = g1.selectbox("Country", ["All"] + countries_all)
    g_type = g2.selectbox("Competition type", ["All"] + sorted(COMP.type.dropna().unique().tolist()))
    rmax = int(max(S.rnk.max(), 2))
    g_rank = g3.slider("Ranking range", 1, rmax, (1, min(50, rmax)))
    fc, fv, fr = COMP.copy(), VEN.copy(), S[S.rnk.between(*g_rank)].copy()
    if g_country != "All":
        fv = fv[fv.country_name == g_country]
        fr = fr[fr.country == g_country]
    if g_type != "All":
        fc = fc[fc.type == g_type]
    st.caption("Competitions carry no country, so the country filter drives venues and players while the type filter drives competitions.")
    kpis([("Competitions", f"{len(fc):,}", f"{fc.category.nunique()} categories", SEQ[0]),
          ("Venues", f"{len(fv):,}", f"{fv.country_name.nunique()} countries", SEQ[1]),
          ("Players", f"{len(fr):,}", f"ranks {g_rank[0]}–{g_rank[1]}", SEQ[2]),
          ("Countries", f"{len(set(fv.country_name.dropna()) | set(fr.country.dropna()))}", "venues ∪ players", SEQ[3])])
    st.write("")
    st.subheader("🌍 Venues vs players by country")
    cmp_ = pd.concat([fv.groupby("country_name").venue_id.count().rename("Venues"),
                      fr.groupby("country").competitor_id.count().rename("Players")], axis=1).fillna(0).astype(int)
    cmp_.index.name = "country"
    cmp_ = cmp_.reset_index()
    cmp_["total"] = cmp_.Venues + cmp_.Players
    if cmp_.empty:
        st.info("No venues or players match the current filters.")
    else:
        a, b = st.columns([1, 2])
        with a: table(cmp_.sort_values("total", ascending=False).drop(columns="total"))
        with b:
            chart(px.bar(cmp_.nlargest(15, "total").melt(id_vars="country", value_vars=["Venues", "Players"], var_name="measure", value_name="count"),
                         x="country", y="count", color="measure", barmode="group", title="Top 15 countries: venues vs ranked players"))
    c1, c2 = st.columns(2)
    if len(fr):
        with c1: chart(px.bar(fr.country.value_counts().head(10).rename_axis("country").reset_index(name="players"), x="players", y="country",
                              orientation="h", title="Top countries by players").update_yaxes(autorange="reversed"))
        with c2: chart(px.scatter(fr, x="rnk", y="points", color="movement", size="events", size_max=16, hover_name="name", hover_data=["country"],
                                  color_continuous_scale="RdYlGn", color_continuous_midpoint=0, title="Ranking vs points"))
    e1, e2 = st.columns(2)
    if len(fc):
        with e1: chart(px.pie(fc.type.value_counts().rename_axis("type").reset_index(name="n"), names="type", values="n", hole=.5, title="Competition type distribution"))
        with e2: chart(px.bar(fc.category.value_counts().head(12).rename_axis("category").reset_index(name="n"), x="n", y="category",
                              orientation="h", title="Category distribution (top 12)").update_yaxes(autorange="reversed"))
    g1_, g2_ = st.columns(2)
    if len(fr):
        with g1_: chart(px.histogram(fr, x="movement", nbins=40, title="Ranking movement distribution", color_discrete_sequence=[SEQ[1]]))
        avg = fr.groupby("country").points.mean().sort_values(ascending=False).head(10).rename("avg_points").reset_index()
        with g2_: chart(px.bar(avg, x="avg_points", y="country", orientation="h", title="Average points by country (top 10)").update_yaxes(autorange="reversed"))
    cxg = fv[fv.complex_name != "—"].groupby("complex_name").size().rename("venues").reset_index().nlargest(10, "venues")
    if len(cxg):
        chart(px.bar(cxg, x="venues", y="complex_name", orientation="h", title="Venues per complex (top 10)").update_yaxes(autorange="reversed"))
    st.subheader("🔥 Top 10 players by points")
    if len(fr): table(view(fr.nlargest(10, "points")), column_config=PTS_CFG)
    else: st.info("No players in the selected rank range / country.")
    with st.expander("🔍 View raw data"):
        st.write("### Competitions"); table(fc)
        st.write("### Venues"); table(fv)
        st.write("### Rankings"); table(view(fr.sort_values("rnk")) if len(fr) else fr)

elif page == PG["search"]:
    hero("Search & Filter Competitors", "Combine name search, rank range, country and points threshold")
    f1, f2 = st.columns([2, 1])
    name = f1.text_input("🔎 Competitor name", placeholder="e.g. Krejcikova")
    min_pts = f2.number_input("Minimum points", 0, int(max(S.points.max(), 1)), 0, step=50)
    f3, f4 = st.columns([1, 2])
    rmax = int(max(S.rnk.max(), 2))
    rr = f3.slider("Rank range", 1, rmax, (1, min(100, rmax)))
    ctry = f4.multiselect("Country", sorted(S.country.unique()))
    R = S[S.rnk.between(*rr) & (S.points >= min_pts)]
    if name: R = R[R.name.str.contains(name, case=False, regex=False)]
    if ctry: R = R[R.country.isin(ctry)]
    if empty(R): st.stop()
    kpis([("Matches", f"{len(R):,}", f"of {len(S):,}", SEQ[0]), ("Countries", f"{R.country.nunique()}", "in result", SEQ[1]),
          ("Avg points", f"{R.points.mean():,.0f}", "", SEQ[2]), ("Best rank", f"{R.rnk.min()}", R.loc[R.rnk.idxmin(), "name"], SEQ[3])])
    st.write("")
    table(view(R.sort_values("rnk")), column_config=PTS_CFG)
    st.download_button("⬇️ Download CSV", R.to_csv(index=False).encode(), "competitors.csv", "text/csv")
    chart(px.scatter(R, x="rnk", y="points", color="country" if R.country.nunique() <= 12 else None, size="events",
                     hover_name="name", title="Filtered competitors: rank vs points"))

elif page == PG["profile"]:
    hero("Competitor Profile", "Rank, movement, competitions played and how the player compares with the field")
    if empty(S): st.stop()
    S = S.reset_index(drop=True)
    names = S.sort_values("rnk").apply(lambda r: f"{r['name']} — {r.country} (#{r.rnk})", axis=1)
    pick = st.selectbox("Select competitor", names.tolist())
    p = S.loc[names[names == pick].index[0]]
    kpis([("Rank", f"#{p.rnk}", p.board, SEQ[0]), ("Movement", f"{int(p.movement):+d}", "vs previous week", "#16A34A" if p.movement >= 0 else "#DC2626"),
          ("Points", f"{int(p.points):,}", "", SEQ[2]), ("Competitions played", f"{int(p.events)}", "", SEQ[1]), ("Country", p.country, p.country_code, SEQ[3])])
    st.write("")
    B = S[S.board == p.board].assign(eff=lambda d: d.points / d.events.clip(lower=1))
    pct = lambda col: float((B[col] <= p[col]).mean() * 100)
    cats, vals = ["Points", "Activity", "Efficiency", "Momentum"], [pct("points"), pct("events"), float((B.eff <= p.points / max(p.events, 1)).mean() * 100), pct("movement")]
    a, b = st.columns(2)
    with a: chart(go.Figure(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself", line_color=SEQ[0]))
                  .update_layout(title="Percentile profile within board", polar=dict(radialaxis=dict(range=[0, 100]))))
    mates = S[(S.country == p.country) & (S.competitor_id != p.competitor_id)].sort_values("rnk")
    b.subheader(f"Compatriots ({len(mates)})")
    with b:
        table(view(mates.head(15)), column_config=PTS_CFG) if len(mates) else st.info("No other ranked players from this country.")
    H = RANKS[RANKS.competitor_id == p.competitor_id].sort_values(["year", "week"])
    if H.period.nunique() > 1:
        chart(px.line(H, x="period", y="rnk", markers=True, title="Rank history").update_yaxes(autorange="reversed"))
    else:
        st.caption("Rank history appears once several weekly snapshots are loaded (etl_weekly.py).")

elif page == PG["country"]:
    hero("Country-Wise Analysis", "Depth (players) vs quality (average points) by nationality")
    if empty(S): st.stop()
    mn = st.slider("Minimum players per country", 1, 20, 1)
    C = (S.groupby(["country", "country_code"]).agg(competitors=("name", "count"), avg_points=("points", "mean"),
         total_points=("points", "sum"), best_rank=("rnk", "min")).reset_index().query("competitors >= @mn").sort_values("total_points", ascending=False))
    if empty(C): st.stop()
    C["avg_points"] = C.avg_points.round(1)
    a, b = st.columns(2)
    with a: table(C.drop(columns="country_code"), column_config={"avg_points": st.column_config.NumberColumn("Avg points", format="%.1f")})
    metric = b.selectbox("Map metric", ["competitors", "avg_points", "total_points"])
    with b: chart(px.choropleth(C, locations="country_code", color=metric, hover_name="country", color_continuous_scale="YlGnBu"))
    chart(px.scatter(C, x="competitors", y="avg_points", size="total_points", color="country", hover_name="country",
                     title="Country strength: depth vs quality").update_layout(showlegend=False))
    chart(px.treemap(C.nlargest(25, "total_points"), path=["country"], values="total_points", color="avg_points",
                     color_continuous_scale="Teal", title="Share of ranking points (top 25 countries)"))

elif page == PG["lead"]:
    hero("Leaderboards", "Top-ranked, highest points, movers and most active competitors")
    if empty(S): st.stop()
    n = st.slider("Rows", 5, 50, 15)
    t = st.tabs(["🥇 Top ranked", "💎 Highest points", "🚀 Climbers", "📉 Fallers", "🔁 Most active"])
    boards_ = {0: S.nsmallest(n, "rnk"), 1: S.nlargest(n, "points"), 2: S.nlargest(n, "movement"),
               3: S.nsmallest(n, "movement"), 4: S.nlargest(n, "events")}
    ycol = {0: "points", 1: "points", 2: "movement", 3: "movement", 4: "events"}
    for i, tab in enumerate(t):
        with tab:
            D = boards_[i]
            table(view(D), column_config=PTS_CFG)
            chart(px.bar(D.sort_values(ycol[i]), x=ycol[i], y="name", orientation="h", color="country", hover_data=["rnk"]), key=f"lb{i}")

elif page == PG["adv"]:
    hero("Advanced Analytics", "Inequality, player tiers, efficiency and correlations — beyond basic reporting")
    if empty(S): st.stop()
    D = S.assign(eff=S.points / S.events.clip(lower=1))
    D["tier"] = pd.qcut(D.points.rank(method="first"), [0, .5, .8, .95, 1], labels=["Emerging", "Challenger", "Contender", "Elite"])
    p = np.sort(D.points.values); cum = np.r_[0, np.cumsum(p) / max(p.sum(), 1)]; x = np.linspace(0, 1, len(cum))
    kpis([("Gini (points)", f"{gini(D.points):.2f}", "0 = equal · 1 = concentrated", SEQ[0]),
          ("Top-10 share", f"{D.nlargest(10, 'points').points.sum() / D.points.sum() * 100:.1f}%", "of all points", SEQ[1]),
          ("Median events", f"{D.events.median():.0f}", "competitions played", SEQ[2]),
          ("Median pts/event", f"{D.eff.median():,.0f}", "efficiency", SEQ[3])])
    st.write("")
    a, b = st.columns(2)
    fig = go.Figure([go.Scatter(x=x, y=cum, fill="tozeroy", name="Lorenz curve", line_color=SEQ[0]),
                     go.Scatter(x=[0, 1], y=[0, 1], name="Perfect equality", line=dict(dash="dash", color="#94A3B8"))])
    with a: chart(fig.update_layout(title="Lorenz curve of ranking points", xaxis_title="Share of players", yaxis_title="Share of points"))
    ts = D.groupby("tier", observed=True).agg(players=("name", "count"), avg_points=("points", "mean"), avg_events=("events", "mean"),
                                              avg_move=("movement", "mean"), pts_per_event=("eff", "mean")).round(1).reset_index()
    with b: chart(px.box(D, x="tier", y="eff", color="tier", points="outliers", title="Efficiency (points/event) by tier",
                         category_orders={"tier": ["Emerging", "Challenger", "Contender", "Elite"]}).update_layout(showlegend=False))
    st.subheader("Player tiers (percentile segmentation)")
    table(ts)
    c, d = st.columns(2)
    me, mp = D.events.median(), D.eff.median()
    with c: chart(px.scatter(D, x="events", y="eff", color="tier", hover_name="name", hover_data=["country", "rnk"],
                             title="Efficiency quadrant (lines = medians)").add_vline(x=me, line_dash="dot").add_hline(y=mp, line_dash="dot"))
    with d: chart(px.imshow(D[["rnk", "points", "movement", "events", "eff"]].corr().round(2), text_auto=True, zmin=-1, zmax=1,
                            color_continuous_scale="RdBu_r", title="Correlation matrix"))
    chart(px.histogram(D, x="movement", nbins=40, title="Distribution of weekly rank movement", color_discrete_sequence=[SEQ[1]]))
    st.caption("Tiers: Emerging = bottom 50% by points · Challenger = 50–80% · Contender = 80–95% · Elite = top 5%.")

elif page == PG["ml"]:
    hero("Machine Learning Intelligence", "Explainable player segmentation, rank estimation and anomaly discovery — built from the selected ranking snapshot")
    if empty(S): st.stop()
    st.caption("Model scope: the selected ranking board and snapshot only. Outputs are analytical estimates, not official SportRadar rankings or match-outcome predictions.")
    try:
        from sklearn.cluster import KMeans
        from sklearn.ensemble import RandomForestRegressor, IsolationForest
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
    except ImportError:
        st.error("Install the machine-learning dependencies to enable this page: pip install scikit-learn")
        st.stop()

    # One row per competitor, with defensively cleaned numeric features.
    M = S[["competitor_id", "name", "country", "rnk", "points", "movement", "events"]].copy()
    for col in ["rnk", "points", "movement", "events"]:
        M[col] = pd.to_numeric(M[col], errors="coerce")
    M = M.replace([np.inf, -np.inf], np.nan).dropna(subset=["rnk", "points", "movement", "events"])
    M = M.drop_duplicates("competitor_id").copy()
    M["points_per_event"] = M.points / M.events.clip(lower=1)
    M["rank_percentile"] = M.rnk.rank(pct=True) * 100
    features = ["rnk", "points", "movement", "events", "points_per_event"]
    model_features = ["points", "movement", "events", "points_per_event"]
    X = M[features].replace([np.inf, -np.inf], np.nan).fillna(0)
    X_model = M[model_features].replace([np.inf, -np.inf], np.nan).fillna(0)

    if len(M) < 12:
        st.warning(f"Only {len(M)} usable competitors are available. Load a larger ranking snapshot (at least 12 rows) for meaningful model analysis.")
        st.stop()

    ml_tabs = st.tabs(["🧩 Player Segmentation", "🎯 Rank Estimator", "🚨 Anomaly Detection", "📊 Model Diagnostics"])
    with ml_tabs[0]:
        st.subheader("Unsupervised player archetypes")
        kmax = min(8, max(2, len(M) // 3))
        k = st.slider("Number of player segments", 2, kmax, min(4, kmax))
        X_scaled = StandardScaler().fit_transform(X)
        M["segment"] = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled).astype(str)
        sil = silhouette_score(X_scaled, M.segment.astype(int)) if len(M) > k and M.segment.nunique() > 1 else float("nan")
        seg = M.groupby("segment").agg(players=("name", "count"), avg_rank=("rnk", "mean"), avg_points=("points", "mean"),
                                       avg_movement=("movement", "mean"), avg_events=("events", "mean"),
                                       avg_points_per_event=("points_per_event", "mean")).reset_index()
        kpis([("Players modelled", f"{len(M):,}", "unique competitors", SEQ[0]),
              ("Segments", str(k), "K-Means clusters", SEQ[1]),
              ("Silhouette score", f"{sil:.3f}" if pd.notna(sil) else "N/A", "higher indicates clearer separation", SEQ[2])])
        a, b = st.columns(2)
        with a: chart(px.scatter(M, x="points", y="rnk", color="segment", size="events", hover_name="name", hover_data=["country", "movement"],
                                 title="Player archetypes: points vs rank").update_yaxes(autorange="reversed"))
        with b: chart(px.bar(seg, x="segment", y="players", color="segment", text="players", title="Segment population"))
        st.markdown("**Segment profile**")
        table(seg.round(2))
        st.download_button("⬇️ Download segmented players", M.to_csv(index=False).encode("utf-8"), "tennis_player_segments.csv", "text/csv")

    with ml_tabs[1]:
        st.subheader("Random Forest rank estimator")
        st.write("Learns the relationship between ranking points, weekly movement and participation volume to estimate rank on held-out records.")
        test_size = st.slider("Test data (%)", 15, 40, 25, 5)
        if len(M) < 20:
            st.info("A larger snapshot is recommended for a more reliable train/test evaluation. Results below are exploratory.")
        X_train, X_test, y_train, y_test = train_test_split(X_model, M["rnk"], test_size=test_size / 100, random_state=42)
        rf = RandomForestRegressor(n_estimators=300, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=-1).fit(X_train, y_train)
        pred = rf.predict(X_test)
        mae = mean_absolute_error(y_test, pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        r2 = r2_score(y_test, pred) if len(y_test) > 1 else float("nan")
        kpis([("Mean absolute error", f"{mae:.1f}", "rank positions", SEQ[0]),
              ("RMSE", f"{rmse:.1f}", "rank positions", SEQ[1]),
              ("R² score", f"{r2:.3f}" if pd.notna(r2) else "N/A", "held-out test set", SEQ[2]),
              ("Training rows", f"{len(X_train):,}", f"Test rows: {len(X_test):,}", SEQ[3])])
        pred_df = pd.DataFrame({"Actual rank": y_test.values, "Estimated rank": pred, "Absolute error": np.abs(y_test.values - pred)})
        a, b = st.columns(2)
        with a: chart(px.scatter(pred_df, x="Actual rank", y="Estimated rank", hover_data=["Absolute error"], title="Held-out actual vs estimated rank"))
        imp = pd.DataFrame({"Feature": model_features, "Importance": rf.feature_importances_}).sort_values("Importance")
        with b: chart(px.bar(imp, x="Importance", y="Feature", orientation="h", title="Random Forest feature importance"))
        st.caption("Interpretation: feature importance describes model reliance, not causation. Since rank and points are closely related in ranking data, treat this as a benchmark model rather than a future-performance forecast.")
        st.download_button("⬇️ Download test predictions", pred_df.to_csv(index=False).encode("utf-8"), "tennis_rank_model_evaluation.csv", "text/csv")

    with ml_tabs[2]:
        st.subheader("Isolation Forest — unusual player profiles")
        contamination = st.slider("Expected anomaly share", 0.01, 0.20, 0.05, 0.01)
        iso_X = StandardScaler().fit_transform(X)
        detector = IsolationForest(contamination=contamination, random_state=42, n_estimators=250)
        labels = detector.fit_predict(iso_X)
        M["profile_status"] = np.where(labels == -1, "Review profile", "Typical profile")
        M["anomaly_score"] = -detector.score_samples(iso_X)
        outliers = M[M.profile_status == "Review profile"].sort_values("anomaly_score", ascending=False)
        kpis([("Profiles reviewed", f"{len(M):,}", "unique competitors", SEQ[0]),
              ("Flagged profiles", f"{len(outliers):,}", f"{contamination:.0%} expected share", SEQ[3]),
              ("Typical profiles", f"{(labels == 1).sum():,}", "within learned pattern", SEQ[1])])
        chart(px.scatter(M, x="points_per_event", y="movement", color="profile_status", size="events", hover_name="name",
                         hover_data=["country", "rnk", "points", "anomaly_score"], title="Unusual profiles by efficiency and weekly movement"))
        st.markdown("**Profiles to review**")
        table(outliers[["name", "country", "rnk", "points", "movement", "events", "points_per_event", "anomaly_score"]].round(2))
        st.caption("Anomaly flags are statistical review signals, not evidence of misconduct, data errors or poor performance.")
        st.download_button("⬇️ Download anomaly review", M.to_csv(index=False).encode("utf-8"), "tennis_anomaly_review.csv", "text/csv")

    with ml_tabs[3]:
        st.subheader("Data quality and model readiness")
        quality = pd.DataFrame({
            "Feature": features,
            "Missing values": [int(M[f].isna().sum()) if f in M else 0 for f in features],
            "Unique values": [int(M[f].nunique()) for f in features],
            "Standard deviation": [float(M[f].std()) if M[f].std() == M[f].std() else 0 for f in features]})
        a, b = st.columns(2)
        with a: chart(px.imshow(X.corr(numeric_only=True).round(2), text_auto=True, aspect="auto", title="Feature correlation matrix",
                                color_continuous_scale="RdBu_r", zmin=-1, zmax=1))
        with b: chart(px.histogram(M, x="points", color="country" if M.country.nunique() <= 8 else None, nbins=30, title="Ranking points distribution"))
        table(quality.round(3))
        st.info("Model note: this page demonstrates feature engineering, unsupervised learning, supervised regression, anomaly detection, model evaluation and explainability using a reproducible random seed.")

elif page == PG["comp"]:
    hero("Competitions Explorer", "Search and filter by type, gender (level) and category")
    srch = st.text_input("🔎 Search competition name", placeholder="e.g. Challenger")
    f = st.columns(3)
    typ = f[0].multiselect("Type", sorted(COMP.type.unique()), default=sorted(COMP.type.unique()))
    gen = f[1].multiselect("Gender / level", sorted(COMP.gender.unique()), default=sorted(COMP.gender.unique()))
    cat = f[2].multiselect("Category", sorted(COMP.category.unique()))
    top_only = st.toggle("Top-level competitions only (no parent)")
    D = COMP[COMP.type.isin(typ) & COMP.gender.isin(gen)]
    if srch: D = D[D.competition_name.str.contains(srch, case=False, na=False, regex=False)]
    if cat: D = D[D.category.isin(cat)]
    if top_only: D = D[D.parent_id.isna()]
    if empty(D): st.stop()
    kpis([("Competitions", f"{len(D):,}", f"of {len(COMP):,}", SEQ[0]), ("Categories", f"{D.category.nunique()}", "", SEQ[1]),
          ("Doubles share", f"{(D.type == 'doubles').mean() * 100:.1f}%", "", SEQ[2]), ("Women's share", f"{(D.gender == 'women').mean() * 100:.1f}%", "", SEQ[3])])
    st.write("")
    a, b = st.columns(2)
    top = D.category.value_counts().head(12).index
    with a: chart(px.sunburst(D[D.category.isin(top)].groupby(["category", "type", "gender"]).size().reset_index(name="n"),
                              path=["category", "type", "gender"], values="n", title="Category → type → gender"))
    par = D.parent_id.value_counts().head(12).rename_axis("competition_id").reset_index(name="subs").merge(COMP[["competition_id", "competition_name"]])
    with b:
        chart(px.bar(par, x="subs", y="competition_name", orientation="h", title="Largest sub-competition trees").update_yaxes(autorange="reversed")) if len(par) else st.info("No sub-competitions in view.")
    chart(px.bar(D.category.value_counts().head(15).rename_axis("category").reset_index(name="competitions"), x="competitions", y="category",
                 orientation="h", title="Category-wise competition count (top 15)").update_yaxes(autorange="reversed"))
    c, d = st.columns(2)
    with c: chart(px.bar(D.type.value_counts().rename_axis("type").reset_index(name="n"), x="type", y="n", color="type", title="Type distribution").update_layout(showlegend=False))
    with d: chart(px.bar(D.gender.value_counts().rename_axis("gender").reset_index(name="n"), x="gender", y="n", color="gender", title="Gender distribution").update_layout(showlegend=False))
    table(D.drop(columns=["parent_id"]).sort_values(["category", "competition_name"]))

elif page == PG["ven"]:
    hero("Venues & Complexes", "Search, filter and explore where tennis is played")
    srch = st.text_input("🔎 Search venue or city")
    f1, f2, f3, f4 = st.columns(4)
    ctry = f1.multiselect("Country", sorted(VEN.country_name.dropna().unique()))
    pool = VEN[VEN.country_name.isin(ctry)] if ctry else VEN
    city = f2.multiselect("City", sorted(pool.city_name.dropna().unique()))
    cxsel = f3.multiselect("Complex", sorted(VEN.complex_name.dropna().unique()))
    tzsel = f4.multiselect("Timezone", sorted(VEN.timezone.dropna().unique()))
    top_n = st.slider("Top N (charts)", 5, 20, 10)
    V = VEN.copy()
    if srch:
        V = V[V.venue_name.str.contains(srch, case=False, na=False, regex=False) | V.city_name.str.contains(srch, case=False, na=False, regex=False)]
    if ctry: V = V[V.country_name.isin(ctry)]
    if city: V = V[V.city_name.isin(city)]
    if cxsel: V = V[V.complex_name.isin(cxsel)]
    if tzsel: V = V[V.timezone.isin(tzsel)]
    if empty(V): st.stop()
    kpis([("Venues", f"{len(V):,}", "", SEQ[0]), ("Countries", f"{V.country_name.nunique()}", "", SEQ[1]),
          ("Complexes", f"{V.complex_name.nunique()}", "", SEQ[2]), ("Timezones", f"{V.timezone.nunique()}", "", SEQ[3])])
    st.write("")
    a, b = st.columns(2)
    vc = V.groupby(["country_name", "country_code"]).size().reset_index(name="venues")
    with a: chart(px.choropleth(vc, locations="country_code", color="venues", hover_name="country_name", color_continuous_scale="YlGnBu", title="Venues by country"))
    with b: chart(px.treemap(vc.nlargest(25, "venues"), path=["country_name"], values="venues", color="venues", color_continuous_scale="Teal", title="Top 25 countries"))
    c, d = st.columns(2)
    cities = V.groupby("city_name").size().rename("venues").reset_index().nlargest(top_n, "venues")
    with c: chart(px.bar(cities, x="venues", y="city_name", orientation="h", title=f"Top {top_n} cities").update_yaxes(autorange="reversed"))
    cx = V[V.complex_name != "—"].groupby("complex_name").size().reset_index(name="venues").query("venues > 1").nlargest(top_n, "venues")
    with d:
        chart(px.bar(cx, x="venues", y="complex_name", orientation="h", color="venues", color_continuous_scale="Oranges",
                     title=f"Complexes with several venues (top {top_n})").update_yaxes(autorange="reversed")) if len(cx) else st.info("No complex hosts more than one venue in this view.")
    tz = V.timezone.value_counts().head(top_n).rename_axis("timezone").reset_index(name="venues")
    chart(px.bar(tz, x="venues", y="timezone", orientation="h", title=f"Venues by timezone (top {top_n})").update_yaxes(autorange="reversed"))
    st.subheader("📌 Venue details")
    vsel = st.selectbox("Select venue", V.venue_name.unique().tolist())
    dtl = V[V.venue_name == vsel].iloc[0]
    d1, d2 = st.columns(2)
    d1.markdown(f"**City:** {dtl.city_name}  \n**Country:** {dtl.country_name}  \n**Timezone:** {dtl.timezone}")
    d2.markdown(f"**Complex:** {dtl.complex_name}  \n**Venue ID:** {dtl.venue_id}  \n**Country code:** {dtl.country_code}")
    with st.expander("🏙️ Venues per country and city"):
        table(V.groupby(["country_name", "city_name"]).size().reset_index(name="venues").sort_values(["venues", "country_name"], ascending=[False, True]))
    table(V.sort_values(["country_name", "city_name"]))

elif page == PG["dq"]:
    hero("Data Quality", "Live integrity checks on the SQL warehouse — completeness, uniqueness and referential integrity")
    tabs = ["categories", "competitions", "complexes", "venues", "competitors", "competitor_rankings"]
    cnt = pd.DataFrame({"table": tabs, "rows": [int(q(f"SELECT COUNT(*) AS n FROM {t}").n[0]) for t in tabs]})
    R = dq_results()
    kpis([("Tables", f"{len(tabs)}", "in warehouse", SEQ[0]), ("Total rows", f"{cnt.rows.sum():,}", "", SEQ[1]),
          ("Checks passed", f"{(R.status == '✅ Pass').sum()}/{len(R)}", "", "#16A34A"), ("Score", f"{(R.status == '✅ Pass').mean() * 100:.0f}%", "data health", SEQ[2])])
    st.write("")
    a, b = st.columns([1, 2])
    with a: table(cnt)
    with b: table(R)
    nulls = pd.concat([COMP.isna().sum().rename("competitions"), VEN.isna().sum().rename("venues"), RANKS[["rnk", "movement", "points", "events", "name", "country"]].isna().sum().rename("rankings")], axis=1).fillna(0).astype(int)
    st.subheader("Null counts (joined views)")
    st.dataframe(nulls, width="stretch")

elif page == PG["report"]:
    report_page()

elif page == PG["sql"]:
    hero("SQL Lab", "Run read-only SQL against the live database — results render as tables and charts")
    PRESET = {
      "Competitions per category": "SELECT k.category_name, COUNT(*) AS competitions FROM competitions c JOIN categories k ON k.category_id = c.category_id GROUP BY k.category_name ORDER BY competitions DESC",
      "Parents with most sub-competitions": "SELECT p.competition_name, COUNT(*) AS subs FROM competitions s JOIN competitions p ON p.competition_id = s.parent_id GROUP BY p.competition_id, p.competition_name ORDER BY subs DESC LIMIT 15",
      "Venues per country": "SELECT country_name, COUNT(*) AS venues FROM venues GROUP BY country_name ORDER BY venues DESC LIMIT 20",
      "Complexes with >1 venue": "SELECT x.complex_name, COUNT(v.venue_id) AS venues FROM complexes x JOIN venues v ON v.complex_id = x.complex_id GROUP BY x.complex_id, x.complex_name HAVING COUNT(v.venue_id) > 1 ORDER BY venues DESC",
      "Top 10 by points": f"SELECT c.name, c.country, r.points, r.{RK} AS rnk FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id ORDER BY r.points DESC LIMIT 10",
      "Competitors per country": "SELECT country, COUNT(*) AS competitors FROM competitors GROUP BY country ORDER BY competitors DESC LIMIT 20",
      "Points by country (Croatia example)": "SELECT c.country, COUNT(*) AS competitors, SUM(r.points) AS total_points FROM competitor_rankings r JOIN competitors c ON c.competitor_id = r.competitor_id WHERE c.country = 'Croatia' GROUP BY c.country",
    }
    choice = st.selectbox("Query library", list(PRESET))
    sql = st.text_area("SQL (SELECT / WITH only)", PRESET[choice], height=140, key=f"sql_{choice}")
    if st.button("▶ Run query", type="primary"):
        if not safe_select(sql): st.error("Only a single read-only SELECT statement is allowed.")
        else:
            try:
                R = q(sql)
                st.success(f"{len(R):,} rows"); table(R)
                num = R.select_dtypes("number").columns
                if len(R) > 1 and len(num) and len(R.columns) > 1:
                    chart(px.bar(R.head(30), x=num[0], y=R.columns[0], orientation="h") if R.columns[0] not in num else px.bar(R.head(30), y=num[0]))
                st.download_button("⬇️ CSV", R.to_csv(index=False).encode(), "query.csv", "text/csv")
            except Exception as e:
                st.error(f"Query failed: {e}")
    with st.expander("Schema"):
        st.code("categories(category_id, category_name)\ncompetitions(competition_id, competition_name, parent_id, type, gender, category_id)\ncomplexes(complex_id, complex_name)\n"
                "venues(venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id)\ncompetitors(competitor_id, name, country, country_code, abbreviation)\n"
                "competitor_rankings(rank_id, rank, movement, points, competitions_played, competitor_id, ranking_name, gender, year, week)")

st.markdown(f'<div class="foot">Built by {AUTHOR} · SportRadar API → SQL → Streamlit · data © Sportradar</div>', unsafe_allow_html=True)