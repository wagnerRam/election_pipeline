
import pandas as pd


def aggregate_results(data: pd.DataFrame) -> pd.DataFrame:
    """Consolida os resultados por UF, turno e candidato."""

    required_columns = {
        "uf",
        "turno",
        "cargo",
        "candidato",
        "partido",
        "votos",
        "percentual",
    }

    missing = required_columns - set(data.columns)
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(missing)}"
        )

    result = data.copy()

    result["votos"] = pd.to_numeric(
        result["votos"], errors="raise"
    )
    result["percentual"] = pd.to_numeric(
        result["percentual"], errors="raise"
    )

    grouped = (
        result.groupby(
            ["uf", "turno", "cargo", "candidato", "partido"],
            as_index=False,
            dropna=False,
        )
        .agg(
            votos=("votos", "sum"),
            percentual_fonte=("percentual", "first"),
        )
        .sort_values(["uf", "votos"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return grouped
