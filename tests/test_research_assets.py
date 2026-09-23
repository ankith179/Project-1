from pathlib import Path


def test_research_catalog_has_required_columns() -> None:
    header = Path("data/catalog.csv").read_text(encoding="utf-8").splitlines()[0].split(",")
    assert {"dataset", "url", "download_status", "sha256", "vigilant_usage"} <= set(header)
