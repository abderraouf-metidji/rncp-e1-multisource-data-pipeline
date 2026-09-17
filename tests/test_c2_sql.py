from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY_DIR = ROOT / "database" / "queries"


def test_at_least_two_sql_queries_exist():
    query_files = sorted(QUERY_DIR.glob("*.sql"))
    assert len(query_files) >= 2


def test_complex_query_contains_expected_features():
    sql = (QUERY_DIR / "02_country_indicators_join.sql").read_text(encoding="utf-8").upper()
    for keyword in ["WITH", "INNER JOIN", "WHERE", "CASE", "ROW_NUMBER", "DENSE_RANK", "ORDER BY"]:
        assert keyword in sql
    assert "SELECT *" not in sql


def test_explain_analyze_is_present():
    sql = (QUERY_DIR / "04_explain_country_indicators.sql").read_text(encoding="utf-8").upper()
    assert "EXPLAIN" in sql
    assert "ANALYZE" in sql
    assert "BUFFERS" in sql


def test_indexes_cover_join_and_filter_columns():
    sql = (ROOT / "database" / "indexes.sql").read_text(encoding="utf-8").upper()
    assert "ISO3" in sql
    assert "YEAR DESC" in sql
    assert "ACTIVE" in sql
