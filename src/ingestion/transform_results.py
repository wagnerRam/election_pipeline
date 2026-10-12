
import pandas as pd


def transform_results(data: pd.DataFrame) -> pd.DataFrame:
    """Converte votos e percentuais para tipos numéricos."""

    required_columns = [
        "uf",
        "eleicao",
        "turno",
        "cargo",
        "candidato",
        "partido",
        "votos",
        "percentual",
        "data_geracao",
        "hora_geracao",
        "coletado_em_utc",
        "ambiente",
    ]

    missing_columns = set(required_columns) - set(data.columns)
    if missing_columns:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(missing_columns)}"
        )

    result = data.copy()

    result["uf"] = result["uf"].astype("string").str.upper()
    result["votos"] = pd.to_numeric(result["votos"], errors="raise").astype("int64")
    result["percentual"] = pd.to_numeric(
        result["percentual"].astype("string").str.replace(",", ".", regex=False),
        errors="raise",
    )

    if (result["votos"] < 0).any():
        raise ValueError("Foram encontrados valores negativos de votos.")

    if (~result["percentual"].between(0, 100)).any():
        raise ValueError("Foram encontrados percentuais fora do intervalo de 0 a 100.")

    return result
