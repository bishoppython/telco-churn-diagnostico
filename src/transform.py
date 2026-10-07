"""Executa os modelos SQL em ordem e materializa o warehouse DuckDB."""
import duckdb

from config import DB, RAW, SQL


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute(f"create or replace view raw_telco as select * from read_csv_auto('{RAW.as_posix()}', header=true, all_varchar=true)")
    for f in sorted(SQL.glob("*.sql")):
        con.execute(f.read_text())
        print(f"OK: {f.name}")
    for t in ["stg_customers", "fct_customer", "mart_churn_segments"]:
        print(f"  {t}: {con.execute(f'select count(*) from {t}').fetchone()[0]:,} linhas")
    con.close()


if __name__ == "__main__":
    main()
