"""P1-5 padding + P1-6 WBI 시각화 PNG 생성."""
import os
import sys

sys.path.insert(0, ".")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import numpy as np

from research_engine.simulation.padding import pad_returns, prices_with_padding
from research_engine.simulation.wbi import generate_wbi

OUT = "dev/active/silver-rev1-phase1/verification/figures"
os.makedirs(OUT, exist_ok=True)

# ── P1-5: JEPI padding 시계열 ────────────────────────────────────────────────
jepi_r = np.load("research_engine/simulation/fixtures/jepi_5y_returns.npy")
TARGET = 2520
padding_len = TARGET - len(jepi_r)

padded_r = pad_returns(jepi_r, TARGET)
prices = prices_with_padding(jepi_r.cumsum()[-1] * 0 + 50.0, padded_r, padding_len)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

ax = axes[0]
x_pad = range(padding_len)
x_act = range(padding_len, TARGET)
ax.fill_between(x_pad, prices[:padding_len], alpha=0.25, color="#aaaaaa", label="Padding 구간 (cyclic)")
ax.plot(x_pad, prices[:padding_len], color="#aaaaaa", linewidth=0.8)
ax.plot(x_act, prices[padding_len:], color="#4e9af1", linewidth=1.2, label="Actual JEPI (2020~)")
ax.axvline(padding_len, color="#e74c3c", linestyle="--", linewidth=1, label="padding / actual 경계")
ax.set_title("P1-5: JEPI padding 시계열 (5년→10년, reverse-cumprod)")
ax.set_xlabel("Trading Day"); ax.set_ylabel("Price ($)")
ax.legend(fontsize=8); ax.spines[["top","right"]].set_visible(False)

ax2 = axes[1]
mean_padded = round(padded_r.mean(), 6)
mean_actual = round(jepi_r.mean(), 6)
ax2.hist(jepi_r, bins=40, alpha=0.6, color="#4e9af1", label=f"Actual mean={mean_actual:.5f}")
ax2.hist(padded_r[:padding_len], bins=40, alpha=0.4, color="#aaaaaa", label=f"Padding mean={mean_padded:.5f}")
ax2.set_title("일별 수익률 분포 비교")
ax2.set_xlabel("Daily return"); ax2.set_ylabel("Count")
ax2.legend(fontsize=8); ax2.spines[["top","right"]].set_visible(False)

plt.tight_layout()
p5_path = f"{OUT}/step-5-padding-jepi.png"
plt.savefig(p5_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"saved: {p5_path}")

# ── P1-6: WBI 가격 시계열 + 수익률 분포 ─────────────────────────────────────
wbi = generate_wbi(TARGET, seed=42)
daily_r = np.diff(wbi) / wbi[:-1]

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

ax = axes[0]
ax.plot(wbi, color="#e67e22", linewidth=1.2)
ax.set_title("P1-6: WBI (Warren Buffett Index) 가격 시계열 (seed=42, 10년)")
ax.set_xlabel("Trading Day"); ax.set_ylabel("Price (KRW 지수)")
ann = (wbi[-1] / 100.0) ** (252 / TARGET) - 1
ax.text(0.02, 0.95, f"seed=42 연환산: {ann:.1%}", transform=ax.transAxes,
        fontsize=8, verticalalignment="top", color="#555")
ax.spines[["top","right"]].set_visible(False)

ax2 = axes[1]
ax2.hist(daily_r, bins=50, color="#e67e22", alpha=0.7)
ax2.axvline(daily_r.mean(), color="#c0392b", linestyle="--", linewidth=1,
            label=f"mean={daily_r.mean():.5f}")
ax2.axvline(0, color="#aaa", linewidth=0.8)
sigma_val = daily_r.std()
ax2.set_title(f"일별 수익률 분포 (σ={sigma_val:.4f} ≈ 1%/일)")
ax2.set_xlabel("Daily return"); ax2.set_ylabel("Count")
ax2.legend(fontsize=8); ax2.spines[["top","right"]].set_visible(False)

plt.tight_layout()
p6_path = f"{OUT}/step-6-wbi-visual.png"
plt.savefig(p6_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"saved: {p6_path}")
