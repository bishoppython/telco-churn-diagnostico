"""Monta o dashboard a partir das métricas calculadas em analyze.py."""
import json

import plotly.graph_objects as go

from config import DOCS, OUT
from report import AMBER, COBALT, NEUTRAL, br, fig_html, kpi, render

m = json.loads((OUT / "metrics.json").read_text())
seg = m["segments"]
LABEL = {"Month-to-month": "Mensal", "One year": "1 ano", "Two year": "2 anos",
         "Electronic check": "Cheque eletrônico", "Mailed check": "Cheque", "Bank transfer (automatic)": "Débito automático",
         "Credit card (automatic)": "Cartão (automático)", "Fiber optic": "Fibra", "DSL": "DSL", "No": "Sem internet"}


def seg_bar(dim, order=None, highlight=None, height=300):
    rows = [r for r in seg if r["dim"] == dim]
    if order:
        rows = sorted(rows, key=lambda r: order.index(r["seg"]))
    x = [LABEL.get(r["seg"], r["seg"]) for r in rows]
    fig = go.Figure(go.Bar(
        x=x, y=[r["churn_rate_pct"] for r in rows],
        marker=dict(color=[AMBER if highlight and r["seg"] in highlight else COBALT for r in rows], cornerradius=4),
        error_y=dict(type="data", symmetric=False, color="#4B5B7E", thickness=1.2, width=4,
                     array=[r["ci_high"] - r["churn_rate_pct"] for r in rows],
                     arrayminus=[r["churn_rate_pct"] - r["ci_low"] for r in rows]),
        text=[f'{br(r["churn_rate_pct"])}%' for r in rows], textposition="auto", insidetextanchor="end",
        textfont=dict(color="#FFFFFF"), outsidetextfont=dict(color="#0C1E46"),
        customdata=[[r["customers"], r["ci_low"], r["ci_high"]] for r in rows],
        hovertemplate="%{x}<br>Churn: %{y}%<br>IC 95%: %{customdata[1]}–%{customdata[2]}%<br>Clientes: %{customdata[0]:,}<extra></extra>"))
    fig.update_yaxes(title="Taxa de churn (%)", rangemode="tozero")
    return fig_html(fig, height)


contract = next(r for r in seg if r["seg"] == "Month-to-month")
two = next(r for r in seg if r["seg"] == "Two year")
new = next(r for r in seg if r["seg"] == "0-6 meses")

assoc = list(reversed(m["association"]))
f_assoc = go.Figure(go.Bar(x=[v for _, v in assoc], y=[k for k, _ in assoc], orientation="h",
                           marker=dict(color=[COBALT if v >= 0.2 else NEUTRAL for _, v in assoc], cornerradius=4),
                           hovertemplate="%{y}: V = %{x:.3f}<extra></extra>"))
f_assoc.update_xaxes(title="Força da associação com o churn (V de Cramér)", range=[0, 0.45])

dec = m["deciles"]
cum = 0; caps = []
for r in dec:
    cum += r["churn_rate"] * r["customers"] / 100
    caps.append(100 * cum / m["churners"])
f_dec = go.Figure(go.Bar(x=[str(r["risk_decile"]) for r in dec], y=[r["churn_rate"] for r in dec],
                         marker=dict(color=[AMBER if r["risk_decile"] <= 2 else COBALT for r in dec], cornerradius=4),
                         customdata=[[c, r["customers"]] for c, r in zip(caps, dec)],
                         text=[f'{br(r["churn_rate"])}%' for r in dec], textposition="outside", cliponaxis=False,
                         hovertemplate="Decil %{x}<br>Churn real: %{y}%<br>Churners acumulados: %{customdata[0]:.0f}%<extra></extra>"))
f_dec.update_xaxes(title="Decil de risco (1 = maior risco previsto)", type="category")
f_dec.update_yaxes(title="Churn real (%)", range=[0, 85])

md = m["model"]; t20 = m["top20"]
sections = [
    {"title": "O contrato mensal concentra o problema",
     "insight": f'Clientes no plano mensal cancelam {br(contract["churn_rate_pct"])}% das vezes, contra {br(two["churn_rate_pct"])}% no contrato de 2 anos. '
                f'O plano mensal responde por {br(100*contract["lost_mrr"]/m["lost_mrr"])}% da receita mensal perdida.',
     "chart": seg_bar("Contrato", ["Month-to-month", "One year", "Two year"], {"Month-to-month"}),
     "note": "As barras de erro mostram o intervalo de confiança de 95% (Wilson)."},
    {"title": "Os primeiros 6 meses são o momento crítico",
     "insight": f'Mais da metade dos clientes novos ({br(new["churn_rate_pct"])}%) cancela nos primeiros 6 meses. Depois de 4 anos, a taxa cai para menos de 10%.',
     "chart": seg_bar("Tempo de casa", ["0-6 meses", "7-12 meses", "13-24 meses", "25-48 meses", "49+ meses"], {"0-6 meses"})},
    {"title": "Contrato, proteção e tempo de casa são os fatores mais associados",
     "insight": "O tipo de contrato tem a associação mais forte com o churn, seguido da quantidade de serviços de proteção (entre clientes com internet), do tempo de casa, do serviço de internet e da forma de pagamento. Gênero e telefone não fazem diferença.",
     "chart": fig_html(f_assoc, 420)},
    {"title": "Serviços de proteção seguram o cliente",
     "insight": "Entre os clientes com internet, o churn cai a cada serviço de proteção contratado (segurança online, backup, proteção de aparelho e suporte técnico).",
     "chart": seg_bar("Serviços de proteção (com internet)", ["0", "1", "2", "3", "4"], {"0"}),
     "note": "Eixo x: quantidade de serviços de proteção contratados."},
    {"title": "O modelo de risco concentra os cancelamentos no topo da lista",
     "insight": f'Nos 20% de clientes com maior risco previsto estão {br(100*t20["churn_capture"],0)}% de todos os cancelamentos e {br(100*t20["lost_mrr_share"],0)}% da receita perdida. '
                f'O modelo tem AUC de {br(md["roc_auc_test"],2)} em dados que ele nunca viu.',
     "chart": fig_html(f_dec, 320),
     "note": "Scores calculados com validação cruzada em 5 partes: cada cliente recebe um score de um modelo que não o viu no treino."},
]
kpis = [kpi(f'{br(m["churn_rate_pct"])}%', f'dos {br(m["customers"],0)} clientes cancelaram'),
        kpi(f'${br(m["lost_mrr"]/1000,0)} mil', f'de receita mensal perdida ({br(m["lost_mrr_pct"])}%)'),
        kpi(f'{br(md["roc_auc_test"],2)}', "AUC do modelo de risco (teste)"),
        kpi(f'{br(100*t20["churn_capture"],0)}%', "dos cancelamentos estão nos 20% de maior risco")]
render(DOCS / "index.html",
       title="Quem cancela e como antecipar o churn",
       level="Nível prata · SQL, Python e análise diagnóstica",
       question="Qual é o perfil de quem cancela, quais fatores mais pesam no churn e como priorizar quem a equipe de retenção deve procurar primeiro.",
       kpis=kpis, sections=sections,
       method="SQL no DuckDB para tipagem, correções e marts por segmento; Python para intervalos de confiança (Wilson), associação (V de Cramér) e uma regressão logística avaliada em teste estratificado. Testes de qualidade rodam no GitHub Actions.",
       source=f'IBM Telco Customer Churn: {br(m["customers"],0)} clientes de uma operadora fictícia criada pela IBM para estudos, com 21 atributos de perfil, serviços, cobrança e churn.',
       repo_url="https://github.com/bishoppython/telco-churn-diagnostico")
print("OK: docs/index.html")
