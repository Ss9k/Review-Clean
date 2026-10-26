from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_clean_endpoint_returns_csv_and_stats_header():
    response = client.post(
        "/clean",
        files={"file": ("reviews.csv", b"review,rating\nGood,5\nGood,5\n,\n", "text/csv")},
        data={"trim_whitespace": "true", "drop_duplicates": "true"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "duplicate_rows_removed=1" in response.headers["x-reviewclean-stats"]
    assert response.content.count(b"Good,5") == 1


def test_clean_endpoint_rejects_non_csv_filename():
    response = client.post("/clean", files={"file": ("reviews.txt", b"hello", "text/plain")})
    assert response.status_code == 400


def test_clean_endpoint_rejects_empty_upload():
    response = client.post("/clean", files={"file": ("reviews.csv", b"", "text/csv")})
    assert response.status_code == 422
