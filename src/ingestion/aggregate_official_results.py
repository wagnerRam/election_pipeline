from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests


URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "votacao_secao/votacao_secao_2026_BR.zip"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

VALID_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

VOTOS_NAO_VALIDOS = {"VOTO BRANCO", "VOTO NULO"}


def normalizar_colunas(data: pd.DataFrame) -> pd.DataFrame:
    """Normaliza os nomes das colunas recebidas do TSE."""
    data.columns = (
        data.columns.astype(str)
        .str.strip()
        .str.strip('"')
    )
    return data


def main():
    print("Baixando resultados oficiais do TSE...")

    response = requests.get(
        URL,
        timeout=(10, 180),
        headers={"User-Agent": "ElectionPipeline/0.3"},
    )
    response.raise_for_status()

    agregacoes = []
    metadata = None

    with ZipFile(BytesIO(response.content)) as archive:
        csv_names = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]

        if not csv_names:
            raise RuntimeError("Nenhum arquivo CSV encontrado no ZIP do TSE.")

        csv_name = next(
            (name for name in csv_names if "votacao_secao" in name.lower()),
            csv_names[0],
        )

        with archive.open(csv_name) as csv_file:
            for chunk in pd.read_csv(
                csv_file,
                sep=";",
                encoding="latin-1",
                dtype=str,
                chunksize=200_000,
                low_memory=False,
            ):
                chunk = normalizar_colunas(chunk)

                colunas_obrigatorias = {
                    "DS_CARGO",
                    "NR_TURNO",
                    "SG_UF",
                    "NM_VOTAVEL",
                    "QT_VOTOS",
                }
                ausentes = colunas_obrigatorias - set(chunk.columns)

                if ausentes:
                    raise RuntimeError(
                        "Colunas obrigatórias ausentes na fonte do TSE: "
                        + ", ".join(sorted(ausentes))
                    )

                if metadata is None:
                    metadata = {
                        "data_geracao": (
                            chunk["DT_GERACAO"].dropna().iloc[0]
                            if "DT_GERACAO" in chunk.columns
                            and not chunk["DT_GERACAO"].dropna().empty
                            else None
                        ),
                        "hora_geracao": (
                            chunk["HH_GERACAO"].dropna().iloc[0]
                            if "HH_GERACAO" in chunk.columns
                            and not chunk["HH_GERACAO"].dropna().empty
                            else None
                        ),
                    }

                chunk["uf"] = chunk["SG_UF"].astype(str).str.strip().str.upper()
                chunk["cargo_descricao"] = (
                    chunk["DS_CARGO"].astype(str).str.strip()
                )
                chunk["cargo"] = (
                    chunk["cargo_descricao"]
                    .str.upper()
                    .str.normalize("NFKD")
                    .str.encode("ascii", errors="ignore")
                    .str.decode("ascii")
                    .str.replace(r"[^A-Z0-9]+", "_", regex=True)
                    .str.strip("_")
                )
                chunk["turno"] = pd.to_numeric(
                    chunk["NR_TURNO"], errors="coerce"
                )
                chunk["eleicao"] = 2026
                chunk["candidato"] = (
                    chunk["NM_VOTAVEL"]
                    .fillna("NÃO INFORMADO")
                    .astype(str)
                    .str.strip()
                )
                chunk["partido"] = ""
                chunk["id_candidato"] = (
                    chunk["SQ_CANDIDATO"].fillna("").astype(str).str.strip()
                    if "SQ_CANDIDATO" in chunk.columns
                    else ""
                )
                chunk["votos"] = pd.to_numeric(
                    chunk["QT_VOTOS"], errors="coerce"
                ).fillna(0).astype("int64")

                chunk = chunk[
                    chunk["uf"].isin(VALID_UFS)
                    & chunk["turno"].isin([1, 2])
                    & chunk["cargo"].ne("")
                    & chunk["cargo"].ne("NAN")
                ].copy()

                if chunk.empty:
                    continue

                chaves = [
                    "uf",
                    "cargo",
                    "cargo_descricao",
                    "turno",
                    "eleicao",
                    "id_candidato",
                    "candidato",
                    "partido",
                ]

                agrupado = (
                    chunk.groupby(
                        chaves,
                        as_index=False,
                        dropna=False,
                    )["votos"]
                    .sum()
                )

                agregacoes.append(agrupado)

    if not agregacoes:
        raise RuntimeError(
            "Nenhum resultado eleitoral foi encontrado na fonte do TSE."
        )

    print("Consolidando os resultados por UF, cargo, turno e candidato...")

    totals = pd.concat(agregacoes, ignore_index=True)

    chaves = [
        "uf",
        "cargo",
        "cargo_descricao",
        "turno",
        "eleicao",
        "id_candidato",
        "candidato",
        "partido",
    ]

    totals = (
        totals.groupby(chaves, as_index=False, dropna=False)["votos"]
        .sum()
    )

    agrupamento_base = ["uf", "cargo", "turno", "eleicao"]

    totals["total_votos_uf"] = totals.groupby(
        agrupamento_base
    )["votos"].transform("sum")

    candidato_normalizado = (
        totals["candidato"].astype(str).str.strip().str.upper()
    )
    validos = ~candidato_normalizado.isin(VOTOS_NAO_VALIDOS)

    votos_validos = (
        totals.loc[validos]
        .groupby(agrupamento_base)["votos"]
        .sum()
        .rename("votos_validos_uf")
    )

    indice = pd.MultiIndex.from_frame(totals[agrupamento_base])
    totals["votos_validos_uf"] = indice.map(votos_validos).astype("float64")

    totals["percentual_total_uf"] = (
        totals["votos"]
        .div(totals["total_votos_uf"].where(totals["total_votos_uf"] != 0))
        .mul(100)
        .fillna(0)
        .round(4)
    )

    totals["percentual_validos"] = (
        totals["votos"]
        .div(totals["votos_validos_uf"].where(totals["votos_validos_uf"] != 0))
        .mul(100)
        .fillna(0)
        .round(4)
    )

    totals.loc[~validos, "percentual_validos"] = 0

    totals["ambiente"] = "oficial"
    totals["fonte"] = "TSE - votação por seção eleitoral"
    totals["data_geracao"] = metadata["data_geracao"] if metadata else None
    totals["hora_geracao"] = metadata["hora_geracao"] if metadata else None
    totals["coletado_em_utc"] = pd.Timestamp.now(tz="UTC").isoformat()

    # Mantém turno como número inteiro no CSV.
    totals["turno"] = totals["turno"].astype(int)

    colunas_saida = [
        "uf",
        "cargo",
        "cargo_descricao",
        "turno",
        "eleicao",
        "id_candidato",
        "candidato",
        "partido",
        "votos",
        "total_votos_uf",
        "votos_validos_uf",
        "percentual_total_uf",
        "percentual_validos",
        "ambiente",
        "fonte",
        "data_geracao",
        "hora_geracao",
        "coletado_em_utc",
    ]

    totals = totals[colunas_saida].sort_values(
        ["cargo", "turno", "uf", "votos"],
        ascending=[True, True, True, False],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "indicadores_oficiais_por_uf.csv"
    temp_file = output_file.with_suffix(".tmp")

    try:
        totals.to_csv(temp_file, index=False, encoding="utf-8")
        temp_file.replace(output_file)
    finally:
        if temp_file.exists():
            temp_file.unlink()

    print(f"\nArquivo gerado: {output_file}")
    print(f"Cargos encontrados: {totals['cargo'].nunique()}")
    print(f"Cargos: {', '.join(sorted(totals['cargo'].unique()))}")
    print(f"Turnos encontrados: {sorted(totals['turno'].unique())}")
    print(f"Estados encontrados: {totals['uf'].nunique()}")
    print(f"Linhas agregadas: {len(totals):,}")
    print(f"Total de votos agregados: {totals['votos'].sum():,}")
    print(f"Data de geração na fonte: {metadata['data_geracao'] if metadata else 'não informada'}")


if __name__ == "__main__":
    main()