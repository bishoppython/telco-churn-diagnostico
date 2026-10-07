"""Testes de qualidade de dados: rodam no CI depois do pipeline."""
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import DB  # noqa: E402


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_um_registro_por_cliente(con):
    assert scalar(con, "select count(*) - count(distinct customer_id) from fct_customer") == 0


def test_sem_nulos_em_campos_criticos(con):
    assert scalar(con, """select count(*) from fct_customer where customer_id is null or churned is null
                          or monthly_charges is null or total_charges is null or tenure_months is null""") == 0


def test_valores_monetarios_nao_negativos(con):
    assert scalar(con, "select count(*) from fct_customer where monthly_charges < 0 or total_charges < 0") == 0


def test_total_zero_somente_para_clientes_novos(con):
    assert scalar(con, "select count(*) from fct_customer where total_charges = 0 and tenure_months > 0") == 0


def test_contratos_conhecidos(con):
    assert scalar(con, """select count(*) from fct_customer
                          where contract not in ('Month-to-month','One year','Two year')""") == 0


def test_segmentos_reconciliam_com_a_base(con):
    total = scalar(con, "select count(*) from fct_customer")
    bad = scalar(con, f"select count(*) from (select dim, sum(customers) n from mart_churn_segments where dim not like '%com internet%' group by dim) where n <> {total}")
    assert bad == 0


def test_scores_cobrem_toda_a_base():
    import json
    m = json.loads((Path(__file__).resolve().parents[1] / "outputs" / "metrics.json").read_text())
    assert m["customers"] == m["scored_customers"]
    assert 0.5 < m["model"]["roc_auc_test"] <= 1
