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
LABEL = {"Month-to-month": "Mensal", "One year": "1 ano", "Two year": "2 anos"}
rows = sorted([r for r in m["segments"] if r["dim"] == "Contrato"], key=lambda r: -r["churn_rate_pct"])
fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
b = ax.bar([LABEL[r["seg"]] for r in rows], [r["churn_rate_pct"] for r in rows],
           color=[AMBER] + [COBALT] * 2, width=0.55,
           yerr=[[r["churn_rate_pct"] - r["ci_low"] for r in rows], [r["ci_high"] - r["churn_rate_pct"] for r in rows]],
           error_kw=dict(ecolor=MUTED, elinewidth=1.2, capsize=4))
ax.bar_label(b, labels=[fmt(r["churn_rate_pct"]) + f'\n{r["customers"]:,} clientes'.replace(",", ".") for r in rows],
             padding=6, color=INK, fontsize=9)
ax.set_ylabel("Taxa de churn"); ax.set_ylim(0, 60); ax.grid(axis="x", visible=False)
ax.set_title("Churn por tipo de contrato (barras de erro: IC 95% de Wilson)")
fig.tight_layout(); fig.savefig(img / "contrato.png"); plt.close(fig)

NOMES = {"cat__contract_Two year": "Contrato de 2 anos", "num__tenure_months": "Tempo de casa (+1 DP)",
         "cat__internet_service_No": "Sem internet", "cat__contract_One year": "Contrato de 1 ano",
         "num__protection_addons": "Serviços de proteção (+1 DP)", "num__streaming_addons": "Serviços de streaming (+1 DP)",
         "cat__multiple_lines_Yes": "Múltiplas linhas", "cat__payment_method_Electronic check": "Cheque eletrônico",
         "cat__internet_service_Fiber optic": "Internet de fibra", "num__paperless_billing": "Fatura digital"}
odds = sorted([r for r in m["odds_ratios"] if r["feature"] in NOMES], key=lambda r: r["odds_ratio"])
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=150)
ax.barh([NOMES[r["feature"]] for r in odds], [r["odds_ratio"] - 1 for r in odds], left=1,
        color=[AMBER if r["odds_ratio"] > 1 else COBALT for r in odds], height=0.6)
for i, r in enumerate(odds):
    ax.text(r["odds_ratio"] + (0.04 if r["odds_ratio"] > 1 else -0.04), i, f'{r["odds_ratio"]:.2f}'.replace(".", ","),
            va="center", ha="left" if r["odds_ratio"] > 1 else "right", color=INK, fontsize=9)
ax.axvline(1, color=MUTED, lw=1); ax.set_xscale("log"); ax.set_xlim(0.16, 3.4)
ax.set_xticks([0.25, 0.5, 1, 2]); ax.set_xticklabels(["0,25", "0,5", "1", "2"]); ax.grid(axis="y", visible=False)
ax.set_xlabel("Razão de chances (escala log): < 1 protege, > 1 aumenta o risco")
ax.set_title("O que aumenta e o que reduz a chance de churn")
fig.tight_layout(); fig.savefig(img / "razao_de_chances.png"); plt.close(fig)
print("OK: docs/img/tempo_de_casa.png, docs/img/decis_de_risco.png, docs/img/contrato.png, docs/img/razao_de_chances.png")
