"""FastAPI service for ReviewClean."""
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.cleaner import clean_csv_bytes

app = FastAPI(title="ReviewClean API", version="1.0.0",
              description="Clean customer-review CSV files and report data-quality metrics.")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "reviewclean-api"}


@app.post("/clean", tags=["cleaning"])
async def clean_csv(
    file: UploadFile = File(...),
    trim_whitespace: bool = Form(True),
    drop_duplicates: bool = Form(True),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Maximum upload size is 10 MB")
    try:
        output, stats, _, _ = clean_csv_bytes(
            content, trim_whitespace=trim_whitespace, drop_duplicates=drop_duplicates
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    headers = {
        "X-ReviewClean-Stats": ";".join(f"{key}={value}" for key, value in stats.items()),
        "Content-Disposition": 'attachment; filename="cleaned_reviews.csv"',
    }
    return Response(content=output, media_type="text/csv; charset=utf-8", headers=headers)
