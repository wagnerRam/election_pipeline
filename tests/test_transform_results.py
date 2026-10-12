
import pandas as pd
import pytest

from src.ingestion.transform_results import transform_results


def sample_data():
    return pd.DataFrame([
        {
            "uf": "sp",
            "eleicao": 21270,
            "turno": 1,
            "cargo": "Presidente",
            "candidato": "Candidato de teste",
            "partido": "Partido de teste",
            "votos": "12345",
            "percentual": "12,34",
            "data_geracao": "29/09/2026",
            "hora_geracao": "16:29:10",
            "coletado_em_utc": "2026-10-12T15:13:52+00:00",
            "ambiente": "simulacao",
        }
    ])


def test_converts_votes_and_percentage():
    result = transform_results(sample_data())

    assert result.loc[0, "votos"] == 12345
    assert result.loc[0, "percentual"] == pytest.approx(12.34)
    assert result.loc[0, "uf"] == "SP"


def test_does_not_modify_original_data():
    original = sample_data()
    before = original.copy(deep=True)

    transform_results(original)

    pd.testing.assert_frame_equal(original, before)


def test_rejects_negative_votes():
    data = sample_data()
    data.loc[0, "votos"] = "-1"

    with pytest.raises(ValueError, match="negativos"):
        transform_results(data)


def test_rejects_percentage_above_100():
    data = sample_data()
    data.loc[0, "percentual"] = "101"

    with pytest.raises(ValueError, match="percentuais"):
        transform_results(data)


def test_rejects_missing_required_columns():
    data = sample_data().drop(columns=["votos"])

    with pytest.raises(ValueError, match="Colunas obrigatórias"):
        transform_results(data)
