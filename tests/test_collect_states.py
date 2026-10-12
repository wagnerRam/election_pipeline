
import time
from threading import Lock

import pandas as pd
import pytest

from src.ingestion import run_pipeline


def fake_candidates(data, uf):
    return [
        {
            "uf": uf.upper(),
            "candidato": "Candidato teste",
            "votos": 100,
        }
    ]


def fake_response(uf):
    return {
        "tpabr": "uf",
        "cdabr": uf.lower(),
    }


def test_collect_all_states_collects_all_ufs(monkeypatch):
    monkeypatch.setattr(
        run_pipeline, "fetch_results", fake_response
    )
    monkeypatch.setattr(
        run_pipeline, "extract_candidates", fake_candidates
    )

    result = run_pipeline.collect_all_states()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(run_pipeline.UF_LIST)
    assert set(result["uf"]) == {
        uf.upper() for uf in run_pipeline.UF_LIST
    }


def test_collect_all_states_rejects_empty_results(monkeypatch):
    monkeypatch.setattr(
        run_pipeline, "fetch_results", fake_response
    )
    monkeypatch.setattr(
        run_pipeline, "extract_candidates",
        lambda data, uf: [],
    )

    with pytest.raises(
        ValueError, match="A coleta não retornou registros"
    ):
        run_pipeline.collect_all_states()


def test_collect_all_states_propagates_collection_failure(
    monkeypatch,
):
    def failing_fetch(uf):
        raise RuntimeError("Falha simulada")

    monkeypatch.setattr(
        run_pipeline, "fetch_results", failing_fetch
    )

    with pytest.raises(RuntimeError, match="Falha simulada"):
        run_pipeline.collect_all_states()


def test_collect_all_states_limits_concurrency(monkeypatch):
    lock = Lock()
    active_requests = 0
    max_active_requests = 0

    def slow_fetch(uf):
        nonlocal active_requests, max_active_requests

        with lock:
            active_requests += 1
            max_active_requests = max(
                max_active_requests, active_requests
            )

        try:
            time.sleep(0.03)
            return {
                "tpabr": "uf",
                "cdabr": uf.lower(),
            }
        finally:
            with lock:
                active_requests -= 1

    monkeypatch.setattr(
        run_pipeline, "fetch_results", slow_fetch
    )
    monkeypatch.setattr(
        run_pipeline, "extract_candidates", fake_candidates
    )

    run_pipeline.collect_all_states()

    assert max_active_requests <= 4
    assert max_active_requests > 1
