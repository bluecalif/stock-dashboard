"""P1-4 backfill row count bar chart 생성."""
import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
# Windows Korean font
plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import matplotlib.patches as mpatches
from sqlalchemy import text
from db.session import SessionLocal

SILVER_ASSETS = ["QQQ","SPY","SCHD","JEPI","TLT","NVDA","GOOGL","TSLA"]
BRONZE_ASSETS = ["KS200","005930","000660","SOXL","BTC","GC=F","SI=F"]
ALL_ASSETS = SILVER_ASSETS + BRONZE_ASSETS

with SessionLocal() as s:
    rows_data = {}
    for a in ALL_ASSETS:
        count = s.execute(text(f"select count(*) from price_daily where asset_id='{a}'")).scalar()
        rows_data[a] = count or 0

colors = ["#4e9af1" if a in SILVER_ASSETS else "#888888" for a in ALL_ASSETS]

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(range(len(ALL_ASSETS)), [rows_data[a] for a in ALL_ASSETS], color=colors, edgecolor="none")

# 기준선
ax.axhline(2520, color="#f1c40f", linestyle="--", linewidth=1, label="10년 기준 (~2520)")
ax.axhline(1260, color="#e67e22", linestyle=":", linewidth=1, label="5년 기준 (~1260, JEPI padding)")

for i, (a, bar) in enumerate(zip(ALL_ASSETS, bars)):
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, h + 20, str(h), ha="center", va="bottom", fontsize=8)

ax.set_xticks(range(len(ALL_ASSETS)))
ax.set_xticklabels(ALL_ASSETS, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("price_daily row count")
ax.set_title("Silver Phase 1 Backfill — 자산별 일봉 row 수 (P1-4)")
ax.set_ylim(0, max(rows_data.values()) * 1.12)

blue_patch = mpatches.Patch(color="#4e9af1", label="Silver gen 신규 8종")
gray_patch = mpatches.Patch(color="#888888", label="Bronze gen 기존 7종")
ax.legend(handles=[blue_patch, gray_patch,
    plt.Line2D([0],[0], color="#f1c40f", linestyle="--", label="10년 기준 (~2520)"),
    plt.Line2D([0],[0], color="#e67e22", linestyle=":", label="5년 기준 (JEPI padding)")],
    loc="lower right", fontsize=8)

ax.spines[["top","right"]].set_visible(False)
ax.set_facecolor("#f9f9f9")
fig.patch.set_facecolor("white")

out = "dev/active/silver-rev1-phase1/verification/figures/step-4-backfill-rowcount.png"
import os; os.makedirs(os.path.dirname(out), exist_ok=True)
plt.tight_layout()
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"saved: {out}")
