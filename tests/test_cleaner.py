import pandas as pd
import pytest

from app.cleaner import clean_csv_bytes, clean_reviews, retry


def test_removes_fully_empty_rows_and_keeps_partial_rows():
    df = pd.DataFrame({"review": ["nice", None, None], "rating": [5, None, 2]})
    cleaned, stats = clean_reviews(df)
    assert len(cleaned) == 2
    assert stats["empty_rows_removed"] == 1
    assert cleaned.iloc[1]["rating"] == 2


def test_removes_exact_duplicates_and_keeps_first():
    df = pd.DataFrame({"review": ["great", "great", "bad"], "rating": [5, 5, 1]})
    cleaned, stats = clean_reviews(df)
    assert cleaned.to_dict("records") == [
        {"review": "great", "rating": 5}, {"review": "bad", "rating": 1}
    ]
    assert stats["duplicate_rows_removed"] == 1


def test_trims_whitespace_before_deduplication():
    df = pd.DataFrame({"review": [" great ", "great"]})
    cleaned, stats = clean_reviews(df, trim_whitespace=True)
    assert cleaned["review"].tolist() == ["great"]
    assert stats["duplicate_rows_removed"] == 1


def test_can_disable_duplicate_removal():
    df = pd.DataFrame({"review": ["same", "same"]})
    cleaned, stats = clean_reviews(df, drop_duplicates=False)
    assert len(cleaned) == 2
    assert stats["duplicate_rows_removed"] == 0


def test_empty_upload_raises_clear_error():
    with pytest.raises(ValueError, match="uploaded CSV is empty"):
        clean_csv_bytes(b"")


def test_csv_bytes_returns_clean_csv_and_stats():
    raw = b"review,rating\nNice,5\nNice,5\n,\n"
    output, stats, source, cleaned = clean_csv_bytes(raw)
    assert b"Nice,5" in output
    assert len(source) == 3
    assert len(cleaned) == 1
    assert stats["rows_removed"] == 2


def test_retry_retries_then_returns_value(monkeypatch):
    calls = {"count": 0}
    monkeypatch.setattr("app.cleaner.time.sleep", lambda _: None)

    @retry(max_attempts=3, delay_seconds=0)
    def sometimes_fails():
        calls["count"] += 1
        if calls["count"] < 3:
            raise OSError("temporary")
        return "ok"

    assert sometimes_fails() == "ok"
    assert calls["count"] == 3


def test_retry_reraises_after_final_attempt(monkeypatch):
    calls = {"count": 0}
    monkeypatch.setattr("app.cleaner.time.sleep", lambda _: None)

    @retry(max_attempts=2, delay_seconds=0, exceptions=(OSError,))
    def always_fails():
        calls["count"] += 1
        raise OSError("still down")

    with pytest.raises(OSError, match="still down"):
        always_fails()
    assert calls["count"] == 2


def test_retry_rejects_invalid_attempt_count():
    with pytest.raises(ValueError, match="at least 1"):
        retry(max_attempts=0)


def test_replaces_missing_cells_and_removes_fully_empty_rows():
    df = pd.DataFrame({
        "review": ["Great", None, None],
        "rating": [5, None, 3],
        "city": [None, None, "Jaipur"],
    })

    cleaned, stats = clean_reviews(df)

    assert len(cleaned) == 2
    assert cleaned.iloc[0].to_dict() == {
        "review": "Great",
        "rating": 5.0,
        "city": "None",
    }
    assert cleaned.iloc[1].to_dict() == {
        "review": "None",
        "rating": 3.0,
        "city": "Jaipur",
    }
    assert stats["empty_rows_removed"] == 1
    
    