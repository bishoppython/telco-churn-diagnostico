"""Diagnóstico de churn: perfil, fatores associados, modelo de risco e receita em jogo."""
import json

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import DB, OUT, RANDOM_STATE

CAT = ["contract", "internet_service", "payment_method", "multiple_lines"]
BOOL = ["paperless_billing", "is_senior", "has_partner", "has_dependents", "has_phone"]
NUM = ["tenure_months", "monthly_charges", "protection_addons", "streaming_addons"]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def cramers_v(x, y):
    t = pd.crosstab(x, y)
    chi2 = chi2_contingency(t, correction=False)[0]
    n = t.values.sum()
    return float(np.sqrt(chi2 / (n * (min(t.shape) - 1))))


def model():
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CAT),
        ("num", StandardScaler(), NUM + BOOL),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=2000))])


def top_share(y, score, frac):
    k = int(np.ceil(frac * len(y)))
    idx = np.argsort(-score)[:k]
    return float(y[idx].sum() / y.sum()), float(y[idx].mean())


def main():
    OUT.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("select * from fct_customer").df()
    seg = con.execute("select * from mart_churn_segments").df()
    for c in BOOL:
        df[c] = df[c].astype(int)
    y = df["churned"].astype(int).to_numpy()

    seg[["ci_low", "ci_high"]] = seg.apply(lambda r: pd.Series(wilson(r.churners, r.customers)), axis=1)

    # Força de associação de cada fator com o churn (Cramér's V; numéricos em faixas).
    assoc_src = {
        "Tipo de contrato": df.contract, "Tempo de casa": df.tenure_band,
        "Serviço de internet": df.internet_service, "Forma de pagamento": df.payment_method,
        "Fatura digital": df.paperless_billing,
        "Valor mensal (quintis)": pd.qcut(df.monthly_charges, 5), "Idoso": df.is_senior,
        "Tem dependentes": df.has_dependents, "Tem parceiro(a)": df.has_partner,
        "Serviços de streaming": df.streaming_addons, "Gênero": df.gender,
        "Telefone": df.has_phone,
    }
    assoc = [(k, round(cramers_v(v, y), 3)) for k, v in assoc_src.items()]
    net = df.internet_service != "No"  # proteção só existe para quem tem internet
    assoc.append(("Serviços de proteção (com internet)", round(cramers_v(df.protection_addons[net], y[net.to_numpy()]), 3)))
    assoc = sorted(assoc, key=lambda kv: -kv[1])

    X = df[CAT + BOOL + NUM]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE)
    m = model().fit(Xtr, ytr)
    p_te = m.predict_proba(Xte)[:, 1]
    rec20, prec20 = top_share(yte, p_te, 0.20)
    rec10, prec10 = top_share(yte, p_te, 0.10)

    # Regra simples de referência: "todo cliente mensal está em risco".
    rule = (Xte.contract == "Month-to-month").to_numpy()
    rule_recall = float(yte[rule].sum() / yte.sum()); rule_precision = float(yte[rule].mean()); rule_share = float(rule.mean())

    # Score fora da amostra para toda a base (5 folds), usado para priorização.
    oof = cross_val_predict(model(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE), method="predict_proba")[:, 1]
    df["risk_score"] = oof
    df["risk_decile"] = pd.qcut(-oof, 10, labels=range(1, 11)).astype(int)
    deciles = df.groupby("risk_decile").agg(customers=("customer_id", "size"), churn_rate=("churned", "mean"),
                                            avg_score=("risk_score", "mean"), lost_mrr=("monthly_charges", lambda s: float(s[df.loc[s.index, "churned"]].sum()))).reset_index()
    deciles["churn_rate"] = (100 * deciles.churn_rate).round(1)
    deciles["avg_score"] = (100 * deciles.avg_score).round(1)

    # Interpretação: razões de chance do modelo ajustado na base toda.
    full = model().fit(X, y)
    names = full.named_steps["pre"].get_feature_names_out()
    coefs = full.named_steps["clf"].coef_[0]
    odds = pd.DataFrame({"feature": names, "coef": coefs, "odds_ratio": np.exp(coefs)}).sort_values("coef")

    top20 = df[df.risk_decile <= 2]
    total_mrr = float(df.monthly_charges.sum())
    lost_mrr = float(df.loc[df.churned, "monthly_charges"].sum())
    top20_lost = float(top20.loc[top20.churned, "monthly_charges"].sum())

    metrics = {
        "customers": int(len(df)), "scored_customers": int(df.risk_score.notna().sum()),
        "churners": int(y.sum()), "churn_rate_pct": round(100 * y.mean(), 1),
        "total_mrr": round(total_mrr, 2), "lost_mrr": round(lost_mrr, 2),
        "lost_mrr_pct": round(100 * lost_mrr / total_mrr, 1),
        "blank_total_charges_fixed": int(((df.total_charges == 0) & (df.tenure_months == 0)).sum()),
        "segments": seg.sort_values(["dim", "churn_rate_pct"], ascending=[True, False]).to_dict(orient="records"),
        "association": assoc,
        "model": {
            "algorithm": "Regressão logística (one-hot + padronização)",
            "test_size": int(len(yte)), "roc_auc_test": round(roc_auc_score(yte, p_te), 3),
            "pr_auc_test": round(average_precision_score(yte, p_te), 3),
            "base_rate_test": round(float(yte.mean()), 3),
            "top20_recall": round(rec20, 3), "top20_precision": round(prec20, 3),
            "top10_recall": round(rec10, 3), "top10_precision": round(prec10, 3),
            "rule_month_to_month": {"share_flagged": round(rule_share, 3), "recall": round(rule_recall, 3), "precision": round(rule_precision, 3)},
            "oof_roc_auc": round(roc_auc_score(y, oof), 3),
        },
        "deciles": deciles.to_dict(orient="records"),
        "top20": {"customers": int(len(top20)), "churners": int(top20.churned.sum()),
                  "churn_capture": round(float(top20.churned.sum() / y.sum()), 3),
                  "lost_mrr": round(top20_lost, 2), "lost_mrr_share": round(top20_lost / lost_mrr, 3)},
        "odds_ratios": odds.round(3).to_dict(orient="records"),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=float))
    df[["customer_id", "risk_score", "risk_decile", "churned", "monthly_charges", "contract", "tenure_band"]] \
        .sort_values("risk_score", ascending=False).to_csv(OUT / "risk_scores.csv", index=False)
    seg.to_csv(OUT / "segments.csv", index=False)
    print(json.dumps({k: metrics[k] for k in ["customers", "churners", "churn_rate_pct", "total_mrr", "lost_mrr", "lost_mrr_pct", "blank_total_charges_fixed"]}, indent=1))
    print(seg.sort_values(["dim", "churn_rate_pct"], ascending=[True, False]).to_string(index=False))
    print(assoc)
    print(json.dumps(metrics["model"], indent=1)); print(json.dumps(metrics["top20"], indent=1))
    print(deciles.to_string(index=False))
    print(odds.to_string(index=False))


if __name__ == "__main__":
    main()
