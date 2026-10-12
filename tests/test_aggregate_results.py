
import pandas as pd
import pytest

from src.ingestion.aggregate_results import aggregate_results


def sample_data():
    return pd.DataFrame([
        {
            "uf": "SP",
            "turno": 1,
            "cargo": "Presidente",
            "candidato": "Candidato A",
            "partido": "Partido A",
            "votos": 100,
            "percentual": 10.0,
        },
        {
            "uf": "SP",
            "turno": 1,
            "cargo": "Presidente",
            "candidato": "Candidato B",
            "partido": "Partido B",
            "votos": 200,
            "percentual": 20.0,
        },
        {
            "uf": "RJ",
            "turno": 1,
            "cargo": "Presidente",
            "candidato": "Candidato A",
            "partido": "Partido A",
            "votos": 50,
            "percentual": 5.0,
        },
    ])


def test_preserves_rows_for_distinct_candidates_and_ufs():
    result = aggregate_results(sample_data())

    assert len(result) == 3
    assert result["uf"].nunique() == 2


def test_preserves_votes_and_source_percentage():
    result = aggregate_results(sample_data())

    row = result[
        (result["uf"] == "SP")
        & (result["candidato"] == "Candidato A")
    ].iloc[0]

    assert row["votos"] == 100
    assert row["percentual_fonte"] == pytest.approx(10.0)


def test_sorts_candidates_by_votes_within_each_state():
    result = aggregate_results(sample_data())

    sp = result[result["uf"] == "SP"]

    assert sp.iloc[0]["candidato"] == "Candidato B"
    assert sp.iloc[1]["candidato"] == "Candidato A"


def test_rejects_missing_required_columns():
    data = sample_data().drop(columns=["votos"])

    with pytest.raises(ValueError, match="Colunas obrigatórias"):
        aggregate_results(data)
