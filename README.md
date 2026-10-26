# ReviewClean — Customer Review Data Quality Studio

A small full-stack CSV-cleaning app with a Streamlit frontend, FastAPI backend, pandas cleaning pipeline, retry decorator, and pytest suite.

## Features
- Upload a customer-review CSV and preview the input.
- Remove fully empty rows and exact duplicate rows.
- Optionally trim whitespace and disable deduplication.
- Preserve partially completed records by default.
- Download a cleaned CSV and view row-level summary metrics.
- FastAPI health check, validation, 10 MB upload cap, and generated OpenAPI docs.
- Retry decorator with configurable attempts, delay, and exception types.

## Setup
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run locally
Open two terminals from the repository root.

Terminal 1 — backend:
```bash
python -m uvicorn app.api:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

Terminal 2 — frontend:
```bash
python -m streamlit run app/frontend.py
```
Frontend: http://localhost:8501

If the API runs elsewhere, set `REVIEWCLEAN_API_URL` to its base URL before launching Streamlit.

## Tests
```bash
python -m pytest -v
```

The suite covers empty-row handling, duplicate handling, whitespace normalization, configurable behavior, invalid uploads, CSV output, retry success/failure, and API endpoints.

## Cleaning rules
1. Empty means every cell in the row is missing or whitespace-only.
2. Duplicate means all values in a row match an earlier row after optional whitespace trimming.
3. The first duplicate is retained.
4. Partially populated rows are preserved; the tool does not assume missing optional fields make a review invalid.
5. Original row order is retained for surviving rows.

## API
`GET /health` returns service status.

`POST /clean` accepts multipart form fields `file`, `trim_whitespace`, and `drop_duplicates`. It returns `text/csv`; summary counters are provided in `X-ReviewClean-Stats`.

## Pull request workflow
```bash
git checkout -b feat/reviewclean-csv-cleaner
git add .
git commit -m "Build ReviewClean CSV cleaning app with tests"
git push -u origin feat/reviewclean-csv-cleaner
```
Then open GitHub and create a pull request from `feat/reviewclean-csv-cleaner` into your default branch. Review the diff, ensure tests pass, and merge the PR if you have repository permission. Do not push directly to the default branch if the assignment specifically requires a PR.
