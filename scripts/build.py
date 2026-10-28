"""Rebuild index.html with the latest nflverse rosters, stats and draft picks.

Run:  python scripts/build.py            (season auto-detected)
      SEASON=2026 python scripts/build.py
"""
import datetime, io, json, os, re, sys, urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
SKILL = ("QB", "RB", "WR", "TE")
FIX = {'OAK':'LV','SD':'LAC','STL':'LA','LAR':'LA','LVR':'LV','NWE':'NE','KAN':'KC','GNB':'GB','SFO':'SF',
       'TAM':'TB','NOR':'NO','SDG':'LAC','JAC':'JAX','ARZ':'ARI','BLT':'BAL','CLV':'CLE','HST':'HOU'}
fx = lambda t: FIX.get(t, t)
today = datetime.date.today()
SEASON = int(os.environ.get("SEASON") or (today.year if today.month >= 8 else today.year - 1))
HISTORY_FROM = 2018

def csv(path):
    url = f"{BASE}/{path}"
    print("fetch", url, file=sys.stderr)
    with urllib.request.urlopen(url) as r:
        return pd.read_csv(io.BytesIO(r.read()), low_memory=False)

def strip(n): return re.sub(r"\s+(Jr\.|Sr\.|II|III|IV)$", "", n)

def age(b):
    b = datetime.date.fromisoformat(b)
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

stars = {tuple(l.strip().split("|")) for l in (ROOT/"scripts/stars.txt").read_text().splitlines() if l.strip()}

# Current rosters: each player's latest week, active or injured reserve, skill positions only
w = csv(f"weekly_rosters/roster_weekly_{SEASON}.csv").sort_values("week").groupby("gsis_id").tail(1)
w = w[(w.week >= w.week.max() - 1) & w.status.isin(["ACT", "RES"]) & w.position.isin(SKILL)]
w = w.dropna(subset=["jersey_number", "height", "birth_date"])
last_week = int(w.week.max())

hist = {}
for y in range(HISTORY_FROM, SEASON):
    try: r = csv(f"rosters/roster_{y}.csv")
    except Exception as e: print("skip", y, e, file=sys.stderr); continue
    for g, t in zip(r.gsis_id, r.team):
        if isinstance(g, str): hist.setdefault(g, set()).add(fx(t))

try: st = csv(f"stats_player/stats_player_reg_{SEASON}.csv").set_index("player_id")
except Exception: st = pd.DataFrame()
dp = csv("draft_picks/draft_picks.csv")
dpg = dp.dropna(subset=["gsis_id"]).drop_duplicates("gsis_id").set_index("gsis_id")

P = []
for _, r in w.iterrows():
    g = r.gsis_id
    s = None
    if len(st) and g in st.index:
        x = st.loc[g]; x = x.iloc[0] if isinstance(x, pd.DataFrame) else x
        s = [int(x.games), int(x.passing_yards), int(x.passing_tds), int(x.passing_interceptions), int(x.carries),
             int(x.rushing_yards), int(x.rushing_tds), int(x.receptions), int(x.receiving_yards), int(x.receiving_tds),
             round(float(x.fantasy_points_ppr), 1)]
    d = None
    if g in dpg.index:
        x = dpg.loc[g]; d = [int(x.season), int(x["round"]), int(x.pick), fx(x.team)]
    P.append({"n": r.full_name, "t": fx(r.team), "p": r.position, "j": int(r.jersey_number), "h": int(r.height),
              "a": age(r.birth_date), "s": int((strip(r.full_name), r.position) in stars),
              "c": r.college.split(";")[0].strip() if isinstance(r.college, str) else "",
              "T": sorted(hist.get(g, set()) | {fx(r.team)}), "st": s, "d": d})

D = {}
for y in sorted(dp.season.unique())[-3:]:
    x = dp[(dp.season == y) & (dp["round"] == 1) & dp.position.isin(SKILL)].sort_values("pick")
    if len(x): D[int(y)] = [[int(a), fx(b), c, e, f] for a, b, c, e, f in zip(x.pick, x.team, x.pfr_player_name, x.position, x.college)]

data = json.dumps({"P": P, "D": D}, separators=(",", ":"))
html = (ROOT/"templates/face-mask.tpl.html").read_text()
html = html.replace("__DATA__", data).replace("__UPDATED__", f"Week {last_week} of the {SEASON} season")
(ROOT/"index.html").write_text(html)
print(f"Built index.html: {len(P)} players, {sum(p['s'] for p in P)} mystery-pool, through week {last_week}", file=sys.stderr)
