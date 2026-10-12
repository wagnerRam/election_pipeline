
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_results_filter_by_sp():
    response = client.get("/api/v1/resultados?uf=SP")

    assert response.status_code == 200

    data = response.json()

    assert data["ambiente"] == "simulacao"
    assert data["filtro_uf"] == "SP"
    assert data["total_registros"] == 13
    assert all(
        item["uf"] == "SP"
        for item in data["resultados"]
    )


def test_results_without_filter():
    response = client.get("/api/v1/resultados")

    assert response.status_code == 200

    data = response.json()

    assert data["total_registros"] == 351
    assert data["filtro_uf"] is None


def test_invalid_uf_length():
    response = client.get("/api/v1/resultados?uf=S")

    assert response.status_code == 422
