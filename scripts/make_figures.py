from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sales.xlsx"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

SHEETS = ["2015", "2016", "2017", "2018", "会员等级"]
sheet_dict = pd.read_excel(DATA, sheet_name=SHEETS)
for year in SHEETS[:-1]:
    frame = sheet_dict[year].dropna()
    frame = frame[frame["订单金额"] > 1].copy()
    frame["max_year_date"] = frame["提交日期"].max()
    frame["year"] = frame["提交日期"].dt.year
    sheet_dict[year] = frame

merged = pd.concat([sheet_dict[year] for year in SHEETS[:-1]], ignore_index=True)
merged["date_intervals"] = (merged["max_year_date"] - merged["提交日期"]).dt.days

rfm = merged.groupby(["year", "会员ID"], as_index=False).agg(
    {"date_intervals": "min", "订单号": "count", "订单金额": "sum"}
)
rfm.columns = ["year", "会员ID", "r", "f", "m"]

r_bins = [-1, 79, 255, 365]
f_bins = [0, 2, 5, 130]
m_bins = [1, 69, 1199, 206252]
rfm["r_label"] = pd.cut(rfm["r"], bins=r_bins, labels=range(len(r_bins) - 1, 0, -1)).astype(str)
rfm["f_label"] = pd.cut(rfm["f"], bins=f_bins, labels=range(1, len(r_bins))).astype(str)
rfm["m_label"] = pd.cut(rfm["m"], bins=m_bins, labels=range(1, len(r_bins))).astype(str)
rfm["rfm_group"] = rfm["r_label"] + rfm["f_label"] + rfm["m_label"]

annual = merged.groupby("year", as_index=False).agg(销售额=("订单金额", "sum"), 订单数=("订单号", "count"))
fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(annual["year"].astype(str), annual["销售额"] / 10000, color="#2F6FB3", label="销售额（万元）")
ax1.set_ylabel("销售额（万元）")
ax1.set_title("年度销售额与订单数")
for i, value in enumerate(annual["销售额"] / 10000):
    ax1.text(i, value + 2, f"{value:.0f}", ha="center", fontsize=10)
ax2 = ax1.twinx()
ax2.plot(annual["year"].astype(str), annual["订单数"], color="#D95F02", marker="o", linewidth=2, label="订单数")
ax2.set_ylabel("订单数")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
fig.tight_layout()
fig.savefig(REPORTS / "annual_sales.png", dpi=160)
plt.close(fig)

group_counts = rfm.groupby("rfm_group", as_index=False).agg(会员数=("会员ID", "count")).sort_values("会员数", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(group_counts["rfm_group"][::-1], group_counts["会员数"][::-1], color="#4C78A8")
ax.set_xlabel("会员数")
ax.set_title("RFM 分群会员数 Top 10")
for i, value in enumerate(group_counts["会员数"][::-1]):
    ax.text(value + 1, i, str(value), va="center", fontsize=9)
fig.tight_layout()
fig.savefig(REPORTS / "rfm_group_distribution.png", dpi=160)
plt.close(fig)

print("saved", REPORTS / "annual_sales.png", REPORTS / "rfm_group_distribution.png")
