import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app, index, metas

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def ensure_index():
    assert index is not None, "Index must be built"
    yield

@ pytest.mark.parametrize("k", [1, 3])
def test_search(k):
    response = client.post(
        "/api/search",
        data={"query": "テスト", "k": k}
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert isinstance(results, list)
    assert len(results) <= k
    for r in results:
        assert "score" in r
        assert "category" in r
        assert "filename" in r
        assert "offset" in r

def test_no_index(monkeypatch):
    monkeypatch.setattr("apps.backend.main.index", None)
    resp = client.post("/api/search", data={"query": "x", "k": 1})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Index not built yet. Run embedding.py first."
