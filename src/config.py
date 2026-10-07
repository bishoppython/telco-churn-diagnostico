from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "telco_customer_churn.csv"
DB = ROOT / "data" / "warehouse.duckdb"
SQL = ROOT / "sql"
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"

SOURCE_URL = ("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
              "master/data/Telco-Customer-Churn.csv")
SOURCE_SHA256 = "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"
RANDOM_STATE = 42
