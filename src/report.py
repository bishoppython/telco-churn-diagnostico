"""Gera o relatório-dashboard estático (docs/index.html) publicado no GitHub Pages."""
import html

import plotly.graph_objects as go
import plotly.io as pio

INK = "#0C1E46"
MUTED = "#4B5B7E"
COBALT = "#1F4FD8"
AMBER = "#C27C0E"
NEUTRAL = "#A9B4CB"
GRID = "#E3E9F4"

pio.templates["portfolio"] = go.layout.Template(layout=dict(
    font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", color=INK, size=13),
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    margin=dict(l=10, r=20, t=10, b=10),
    xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED)),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID, font=dict(color=INK)),
    showlegend=False, bargap=0.35,
))
pio.templates.default = "portfolio"


def br(x, nd=1):
    """Formata número no padrão brasileiro (vírgula decimal, ponto de milhar)."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fig_html(fig, height=340):
    fig.update_layout(height=height, separators=",.", margin=dict(l=10, r=30, t=10, b=10))
    fig.update_xaxes(automargin=True, title_standoff=12)
    fig.update_yaxes(automargin=True, title_standoff=12)
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={"displayModeBar": False, "responsive": True})


def kpi(value, label):
    return f'<div class="kpi"><b>{html.escape(str(value))}</b><span>{html.escape(label)}</span></div>'


def render(path, *, title, level, question, kpis, sections, method, source, repo_url):
    body = "\n".join(
        f'<section class="card"><h2>{html.escape(s["title"])}</h2>'
        f'<p class="insight">{s["insight"]}</p>{s["chart"]}'
        + (f'<p class="note">{s["note"]}</p>' if s.get("note") else "") + "</section>"
        for s in sections)
    page = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{{--ink:{INK};--muted:{MUTED};--cobalt:{COBALT};--grid:{GRID};--paper:#F3F6FB}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 "IBM Plex Sans",Segoe UI,sans-serif}}
.wrap{{max-width:1040px;margin:0 auto;padding-inline:20px;padding-block:40px 56px}}
.level{{font:500 .8rem "IBM Plex Mono",monospace;color:var(--cobalt)}}
h1,h2{{font-family:"Bricolage Grotesque",Segoe UI,sans-serif;margin:0;text-wrap:balance}}
h1{{font-size:clamp(2rem,4.5vw,3rem);line-height:1.05;margin:8px 0 14px}}
h2{{font-size:1.3rem;line-height:1.25;margin-bottom:8px}}
.q{{font-size:1.1rem;max-width:62ch;color:var(--muted)}}
.kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:28px 0}}
.kpi{{background:#fff;border:1px solid var(--grid);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:2px}}
.kpi b{{font:800 1.6rem "Bricolage Grotesque",sans-serif;font-variant-numeric:tabular-nums}}
.kpi span{{font-size:.85rem;color:var(--muted)}}
.card{{background:#fff;border:1px solid var(--grid);border-radius:12px;padding:20px 20px 12px;margin-top:18px;min-width:0}}
.insight{{max-width:70ch;margin:0 0 10px}}
.note{{font-size:.85rem;color:var(--muted);margin:6px 0 8px}}
.meta{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px;margin-top:18px}}
.meta div{{background:#fff;border:1px solid var(--grid);border-radius:12px;padding:18px 20px}}
.meta h3{{margin:0 0 6px;font-size:1rem}} .meta p{{margin:0;color:var(--muted);font-size:.95rem}}
footer{{margin-top:28px;font-size:.9rem;color:var(--muted)}} a{{color:var(--cobalt)}}
@media (max-width:760px){{.kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}.meta{{grid-template-columns:minmax(0,1fr)}}}}
</style></head>
<body><main class="wrap">
<div class="level">{html.escape(level)}</div>
<h1>{html.escape(title)}</h1>
<p class="q">{question}</p>
<div class="kpis">{"".join(kpis)}</div>
{body}
<div class="meta"><div><h3>Como foi feito</h3><p>{method}</p></div><div><h3>Fonte dos dados</h3><p>{source}</p></div></div>
<footer>Projeto de <a href="https://bishoppython.github.io">Anderson Bispo</a> · código e metodologia em <a href="{repo_url}">{html.escape(repo_url.replace("https://", ""))}</a></footer>
</main></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
