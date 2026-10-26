from __future__ import annotations

import io
import time
from functools import wraps
from typing import Callable, TypeVar, ParamSpec     #Type Hints

import pandas as pd

P = ParamSpec("P")
R = TypeVar("R")


def retry(max_attempts: int = 3, delay_seconds: float = 0.2,
          exceptions: tuple[type[BaseException], ...] = (Exception,)):
    """Retry a function on selected exceptions, then re-raise the last error."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts:
                        raise
                    if delay_seconds:
                        time.sleep(delay_seconds)
            raise RuntimeError("Unreachable retry state")
        return wrapped
    return decorate


@retry(max_attempts=3, delay_seconds=0.05, exceptions=(UnicodeDecodeError,))
def read_csv_bytes(content: bytes) -> pd.DataFrame:
    """Read uploaded CSV bytes with UTF-8 and UTF-8-BOM support."""
    try:
        return pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")       #io.BytesIO(content): Bytes ko memory mein file-like object banata hai.
    except UnicodeDecodeError:
        return pd.read_csv(io.BytesIO(content), encoding="latin-1")


def clean_reviews(df: pd.DataFrame, *, trim_whitespace: bool = True, drop_duplicates: bool = True) -> tuple[pd.DataFrame, dict[str, int]]:
    """Remove fully empty rows and exact duplicates; preserve partial rows.

    Whitespace-only cells are treated as empty when trim_whitespace is enabled.
    Duplicate detection happens after whitespace normalization.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    result = df.copy()
    original_rows = len(result)
    original_columns = len(result.columns)

    if trim_whitespace:
        for column in result.select_dtypes(include=["object", "string"]).columns:
            result[column] = result[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )

    # Convert blank strings to NA for emptiness checks, without forcing all values to strings.
    emptiness_view = result.replace(r"^\s*$", pd.NA, regex=True)
    empty_mask = emptiness_view.isna().all(axis=1)
    empty_rows_removed = int(empty_mask.sum())
    result = result.loc[~empty_mask].copy()

    duplicate_rows_removed = 0
    if drop_duplicates:
        before = len(result)
        result = result.drop_duplicates(keep="first")
        duplicate_rows_removed = before - len(result)

    stats = {
        "original_rows": original_rows,
        "cleaned_rows": len(result),
        "empty_rows_removed": empty_rows_removed,
        "duplicate_rows_removed": duplicate_rows_removed,
        "rows_removed": original_rows - len(result),
        "columns": original_columns,
    }
    return result.reset_index(drop=True), stats


def clean_csv_bytes(content: bytes, *, trim_whitespace: bool = True,
                    drop_duplicates: bool = True) -> tuple[bytes, dict[str, int], pd.DataFrame, pd.DataFrame]:
    """Validate and clean CSV bytes, returning output bytes, stats, source and result."""
    if not content:
        raise ValueError("The uploaded CSV is empty")
    try:
        source = read_csv_bytes(content)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The CSV has no header or data") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    if len(source.columns) == 0:
        raise ValueError("The CSV must contain at least one column")
    cleaned, stats = clean_reviews(
        source, trim_whitespace=trim_whitespace, drop_duplicates=drop_duplicates
    )
    output = cleaned.to_csv(index=False).encode("utf-8")
    return output, stats, source, cleaned
