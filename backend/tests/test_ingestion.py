from pathlib import Path

from app.services.ingestion import load_and_clean


def test_supplied_workbook_has_expected_clean_rows():
    workbook = Path(__file__).resolve().parents[2] / "data" / "sample_delay_logs.xlsx"
    dataframe = load_and_clean(workbook)
    assert len(dataframe) == 209
    assert dataframe["Eff Durn"].notna().all()
    assert dataframe["Delay Date"].notna().all()
