"""Gera as imagens estáticas usadas no README."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import DOCS, OUT  # noqa: E402

INK, MUTED, COBALT, AMBER, GRID = "#0C1E46", "#4B5B7E", "#1F4FD8", "#C27C0E", "#E3E9F4"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": INK,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "axes.axisbelow": True, "axes.titleweight": "bold", "axes.titlesize": 13,
                     "axes.titlecolor": INK, "axes.titlelocation": "left"})
m = json.loads((OUT / "metrics.json").read_text())
img = DOCS / "img"; img.mkdir(parents=True, exist_ok=True)
fmt = lambda v: f"{v:.1f}%".replace(".", ",")  # noqa: E731

order = ["0-6 meses", "7-12 meses", "13-24 meses", "25-48 meses", "49+ meses"]
rows = sorted([r for r in m["segments"] if r["dim"] == "Tempo de casa"], key=lambda r: order.index(r["seg"]))
fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
b = ax.bar([r["seg"] for r in rows], [r["churn_rate_pct"] for r in rows], color=[AMBER] + [COBALT] * 4, width=0.6)
ax.bar_label(b, labels=[fmt(r["churn_rate_pct"]) for r in rows], padding=3, color=INK)
ax.set_ylabel("Taxa de churn"); ax.set_ylim(0, 62); ax.grid(axis="x", visible=False)
ax.set_title("Churn por tempo de casa")
fig.tight_layout(); fig.savefig(img / "tempo_de_casa.png"); plt.close(fig)

dec = m["deciles"]
fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
b = ax.bar([str(r["risk_decile"]) for r in dec], [r["churn_rate"] for r in dec],
           color=[AMBER if r["risk_decile"] <= 2 else COBALT for r in dec], width=0.6)
ax.bar_label(b, labels=[fmt(r["churn_rate"]) for r in dec], padding=3, color=INK, fontsize=9)
ax.set_xlabel("Decil de risco previsto (1 = maior risco)"); ax.set_ylabel("Churn real"); ax.set_ylim(0, 85)
ax.grid(axis="x", visible=False); ax.set_title("Churn real por decil de risco do modelo")
fig.tight_layout(); fig.savefig(img / "decis_de_risco.png"); plt.close(fig)
print("OK: docs/img/tempo_de_casa.png, docs/img/decis_de_risco.png")
